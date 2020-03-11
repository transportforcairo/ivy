'''
Prep config.
'''
import os


def fetch_vid(url):
    '''
    Download requested video
    '''
    import requests
    from tqdm import tqdm

    local_filename = url.split('/')[-1]

    with requests.get(url, stream=True) as req:
        header = req.headers

        # Check type of download is file
        content_type = header.get('content-type')
        if 'text' in content_type.lower():
            print("Invalid URL. Received {}".format(content_type))
            return
        if 'html' in content_type.lower():
            print("Invalid URL. Received {}".format(content_type))
            return

        if req.status_code == 200:
            print("Fetched Successfully!")

            # Display download progress bar
            print("Downloading...")
            total_size = int(req.headers.get('content-length', 0))
            block_size = 1024  # 1 Kilobyte
            transfer = tqdm(total=total_size, unit='iB', unit_scale=True)
            with open('./data/videos/{}'.format(local_filename), 'wb') as file:
                for data in req.iter_content(block_size):
                    transfer.update(len(data))
                    file.write(data)
            transfer.close()
            if total_size != 0 and transfer.n != total_size:
                print("ERROR, something went wrong")

        req.raise_for_status()

    return './data/videos/{}'.format(local_filename)


def initialize_ivy():
    '''
    Docker entry point
    '''

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--video", required=True, help="Video URL")
    parser.add_argument("-c", "--class", required=True,
                        help="Classes of Interest")
    args = vars(parser.parse_args())
    vid_url = args["video"]
    classes_of_interest = args["class"].strip("[]").split(",")

    with open(os.getenv('YOLO_CLASSES_OF_INTEREST_PATH'), 'w+') as coi_file:
        for coi in classes_of_interest:
            coi_file.write(f"{coi}\n")

    print("Fetching video from: {}".format(vid_url))

    path2vid = fetch_vid(vid_url)

    os.environ['VIDEO'] = path2vid


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    from util.logger import init_logger
    init_logger()

    initialize_ivy()

    from main import run
    run()
