'''
Prep config.
'''
import os


def fetch_vid(url):
    '''
    Download requested video
    '''
    import requests

    local_filename = url.split('/')[-1]

    with requests.get(url, stream=True) as req:
        header = req.headers
        content_type = header.get('content-type')
        if 'text' in content_type.lower():
            print("Invalid URL. Received {}".format(content_type))
            return
        if 'html' in content_type.lower():
            print("Invalid URL. Received {}".format(content_type))
            return
        req.raise_for_status()

        if req.status_code == 200:
            print("Fetched Successfully!")
            with open('./data/videos/{}'.format(local_filename), 'wb') as file:
                file.write(req.content)

    return ('./data/videos/{}'.format(local_filename))


def initialize_ivy():
    '''
    Docker entry point
    '''

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--video", required=True, help="Video URL")
    args = vars(parser.parse_args())
    vid_url = args["video"]

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
