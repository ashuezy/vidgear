"""
===============================================
vidgear library source-code is deployed under the Apache 2.0 License:

Copyright (c) 2019-2020 Abhishek Thakur(@abhiTronix) <abhi.una12@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
===============================================
"""
# import the necessary packages

import os
import sys
import numpy as np
import pytest
import asyncio
import logging as log
import tempfile

from vidgear.gears import NetGear, VideoGear
from vidgear.gears.asyncio import NetGear_Async
from vidgear.gears.asyncio.helper import logger_handler

from .fps import FPS

# define test logger
logger = log.getLogger("Benchmark NetworkGears")
logger.propagate = False
logger.addHandler(logger_handler())
logger.setLevel(log.DEBUG)


def return_testvideo_path():
    """
    returns Test Video path
    """
    path = "{}/Downloads/Test_videos/BigBuckBunny_4sec.mp4".format(
        tempfile.gettempdir()
    )
    return os.path.abspath(path)


async def client_iterator(client):
    # loop over Client's Asynchronous Frame Generator
    fps_async = FPS().start()
    async for frame in client.recv_generator():
        # check if NoneType
        if frame is None:
            break
        fps_async.update()
        # await before continuing
        await asyncio.sleep(0.000001)
    logger.info("NetGear_Async approx. FPS: {:.2f}".format(fps_async.average_fps()))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_benchmark_Netgear_Async():
    """
    Benchmark NetGear Async in FPS
    """
    try:
        # launch server with valid source
        server = NetGear_Async(
            source=return_testvideo_path(), pattern=1, logging=True
        ).launch()
        # launch client
        client = NetGear_Async(receive_mode=True, pattern=1, logging=True).launch()
        # gather and run tasks
        input_coroutines = [server.task, client_iterator(client)]
        res = await asyncio.gather(*input_coroutines, return_exceptions=True)
    except Exception as e:
        pytest.fail(str(e))
    finally:
        # close
        server.close(skip_loop=True)
        client.close(skip_loop=True)


def test_benchmark_NetGear():
    """
    Benchmark NetGear original in FPS
    """
    try:
        # open stream with valid source
        stream = VideoGear(source=return_testvideo_path()).start()
        # open server and client
        client = NetGear(receive_mode=True, pattern=1, logging=True)
        server = NetGear(pattern=1, logging=True)
        # start FPS handler
        fps = FPS().start()
        # playback
        while True:
            frame_server = stream.read()
            if frame_server is None:
                break
            fps.update()  # update
            server.send(frame_server)  # send
            frame_client = client.recv()  # recv
        stream.stop()
    except Exception as e:
        pytest.fail(str(e))
    finally:
        # close
        server.close()
        client.close()
        logger.info("NetGear approx. FPS: {:.2f}".format(fps.average_fps()))
