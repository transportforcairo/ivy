'''
VCS entry point.
'''


def run():
    '''
    Initialize counter class and run counting loop.
    '''

    import ast
    import os
    import time
    import cv2
    import json
    from util.image import take_screenshot
    from util.logger import get_logger
    from util.debugger import mouse_callback
    from VehicleCounter import VehicleCounter

    logger = get_logger()

    # capture traffic scene video
    is_cam = ast.literal_eval(os.getenv('IS_CAM'))
    video = int(os.getenv('VIDEO')) if is_cam else os.getenv('VIDEO')
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise Exception('Invalid video source {0}'.format(video))
    ret, frame = cap.read()
    f_height, f_width, _ = frame.shape

    detection_interval = int(os.getenv('DI'))
    mcdf = int(os.getenv('MCDF'))
    mctf = int(os.getenv('MCTF'))
    detector = os.getenv('DETECTOR')
    tracker = os.getenv('TRACKER')
    # create detection region of interest polygon
    use_droi = ast.literal_eval(os.getenv('USE_DROI'))
    droi = ast.literal_eval(os.getenv('DROI')) \
        if use_droi \
        else [(0, 0), (f_width, 0), (f_width, f_height), (0, f_height)]
    show_droi = ast.literal_eval(os.getenv('SHOW_DROI'))
    counting_lines = ast.literal_eval(os.getenv('COUNTING_LINES'))
    show_counts = ast.literal_eval(os.getenv('SHOW_COUNTS'))

    vehicle_counter = VehicleCounter(frame, detector, tracker, droi, show_droi, mcdf,
                                     mctf, detection_interval, counting_lines, show_counts)

    record = ast.literal_eval(os.getenv('RECORD'))
    headless = ast.literal_eval(os.getenv('HEADLESS'))
    out_video_path = os.path.join(os.getcwd(), os.getenv('OUTPUT_VIDEO_PATH'))
    print("OUTPUT_VIDEO_PATH", out_video_path)
    if record:
        # initialize video object to record counting
        output_video = cv2.VideoWriter(out_video_path,
                                       cv2.VideoWriter_fourcc(*'MP4V'),
                                       30,
                                       (f_width, f_height))

    logger.info('Processing started.', extra={
        'meta': {
            'label': 'START_PROCESS',
            'counter_config': {
                'di': detection_interval,
                'mcdf': mcdf,
                'mctf': mctf,
                'detector': detector,
                'tracker': tracker,
                'use_droi': use_droi,
                'droi': droi,
                'show_droi': show_droi,
                'counting_lines': counting_lines
            },
        },
    })

    if not headless:
        # capture mouse events in the debug window
        cv2.namedWindow('Debug')
        cv2.setMouseCallback('Debug', mouse_callback, {
                             'frame_width': f_width, 'frame_height': f_height})

    is_paused = False
    output_frame = None

    # main loop
    while is_cam or cap.get(cv2.CAP_PROP_POS_FRAMES) + 1 < cap.get(cv2.CAP_PROP_FRAME_COUNT):
        k = cv2.waitKey(1) & 0xFF
        if k == ord('p'):  # pause/play loop if 'p' key is pressed
            is_paused = False if is_paused else True
            logger.info('Loop paused/played.',
                        extra={'meta': {'label': 'PAUSE_PLAY_LOOP', 'is_paused': is_paused}})
        if k == ord('s') and output_frame is not None:  # save frame if 's' key is pressed
            take_screenshot(output_frame)
        if k == ord('q'):  # end video loop if 'q' key is pressed
            logger.info('Loop stopped.', extra={
                        'meta': {'label': 'STOP_LOOP'}})
            break

        if is_paused:
            time.sleep(0.5)
            continue

        _timer = cv2.getTickCount()  # set timer to calculate processing frame rate

        if ret:
            vehicle_counter.count(frame)
            output_frame = vehicle_counter.visualize()

            if record:
                output_video.write(output_frame)

            if not headless:
                debug_window_size = ast.literal_eval(
                    os.getenv('DEBUG_WINDOW_SIZE'))
                resized_frame = cv2.resize(output_frame, debug_window_size)
                cv2.imshow('Debug', resized_frame)

        processing_frame_rate = round(
            cv2.getTickFrequency() / (cv2.getTickCount() - _timer), 2)
        frames_processed = round(cap.get(cv2.CAP_PROP_POS_FRAMES))
        frames_count = round(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.debug('Frame processed.', extra={
            'meta': {
                'label': 'FRAME_PROCESS',
                'frames_processed': frames_processed,
                'frame_rate': processing_frame_rate,
                'frames_left': frames_count - frames_processed,
                'percentage_processed': round((frames_processed / frames_count) * 100, 2),
            },
        })

        ret, frame = cap.read()

    # end capture, close window, close log file and video object if any
    cap.release()
    if not headless:
        cv2.destroyAllWindows()
    if record:
        output_video.release()
    logger.info('Processing ended.', extra={'meta': {'label': 'END_PROCESS'}})

    # post final counts
    import requests
    import mimetypes

    final_counts = vehicle_counter.counts
    job_id = int(os.environ['JOB_ID'])
    posting_url = os.environ['API_HOST'] + os.environ['API_URL']

    # Upload final counts to db
    def update_job():
        update_job_mutation = """
        mutation UpdateJob($jobId: Float!, $count: String!, $cmd: String!){
            updateJob(
                jobId: $jobId
                count: $count
                cmd: $cmd
            ) {
                status
            }
        }
        """
        update_variables = {
            "jobId": job_id,
            "count": json.dumps(final_counts),
            "cmd": "completed"
        }

        update_final_counts = requests.post(
            posting_url, json={'query': update_job_mutation, 'variables': update_variables})

        if update_final_counts.status_code == 200:
            print(update_final_counts.json())
        else:
            raise Exception("Query failed to run by returning code of {}. {}. {}.".format(
                update_final_counts.status_code, update_job_mutation, update_final_counts.json()))

    update_job()

    # Get presigned URL, auth to upload
    def s3_sign(file):
        """
        Get presigned url to auth upload
        """
        sign_mutation = """
        mutation JobCompleteSignS3($filetype: String!, $jobId: Float!) {
            jobCompleteSignS3 (filetype: $filetype, jobId: $jobId){
                    signedRequest	
                    url
                }
        }
        """
        variables = {
            "filetype": mimetypes.guess_type(file.name)[0],
            "jobId": job_id
        }
        sign_response = requests.post(posting_url, json={
            'query': sign_mutation, 'variables': variables})
        if sign_response.status_code == 200:
            print(sign_response.json())
            return sign_response
        else:
            raise Exception("Query failed to run by returning code of {}. {}. {}.".format(
                sign_response.status_code, sign_mutation, sign_response.json()))

    # Send put request to AWS S3 with file
    def upload_to_s3(file, signed_request):
        """
        Upload output file to S3
        """
        headers = {
            "Content-Type": mimetypes.guess_type(file.name)[0]
        }
        s3_upload = requests.put(signed_request, data=file, headers=headers)

        if s3_upload.status_code == 200:
            print(s3_upload.json())
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(
                s3_upload.status_code, s3_upload.json()))

    # Index uploaded file in db
    def add_to_db(file, url, filename):
        """
        Index uploaded file in DB
        """
        create_video_mutation = """
        mutation CreateVideo($jobId: Float!, $filename: String!, $size: Float!, $URI: String!) {
            createProcessedVideo(
                jobId: $jobId
                name: $filename
                size: $size
                URI: $URI
            ) {
                id
            }
        }
        """
        variables = {
            "jobId": job_id,
            "filename": filename,
            "size": os.stat(file.name).st_size,
            "url": url
        }
        add_db_index = requests.post(posting_url, json={
            'query': create_video_mutation, 'variables': variables})

        if add_db_index.status_code == 200:
            print(add_db_index.json())
        else:
            raise Exception("Query failed to run by returning code of {}. {}. {}.".format(
                add_db_index.status_code, create_video_mutation, add_db_index.json()))

    # Trigger upload process
    def start_uploading():
        """
        Upload file flow
        """
        presigned_url = ''
        location_url = ''
        with open(out_video_path, 'rb') as f:
            response = s3_sign(f)
            if response.status_code == 200:
                presigned_url = response.json(
                )['data']['jobCompleteSignS3']['signedRequest']
                location_url = response.json(
                )['data']['jobCompleteSignS3']['url']
                print("signed: {}\nfinal destination: {}".format(
                    presigned_url, location_url))
            else:
                raise Exception("Query failed to run by returning code of {} during upload".format(
                    response.status_code))

        new_out_video_path = os.path.join(
            os.getcwd(), location_url.split("/")[-1]+".mp4")
        print("New OUTPUT_VIDEO_PATH", new_out_video_path)
        os.rename(out_video_path, new_out_video_path)
        with open(new_out_video_path, 'rb') as f:
            upload_to_s3(f, presigned_url)
            add_to_db(f, location_url, new_out_video_path)

    start_uploading()
