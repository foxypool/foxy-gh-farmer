from asyncio import sleep
from logging import getLogger

from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex

import aioudp


def map_priority_to_log_level(priority: int) -> int:
    level = priority - 8
    if level == 7:
        return 10
    if level == 6:
        return 20
    if level == 4:
        return 30
    if level == 3:
        return 40
    if level == 2:
        return 50

    return 0


class Parser(object):
    def __init__(self):
        ints = Word(nums)

        # priority
        priority = Suppress("<") + ints + Suppress(">")

        # service
        hostname = Word(alphas + nums + "_" + "-" + ".")

        # message
        message = Regex(".*")

        # pattern build
        self.__pattern = priority + hostname + message

    def parse(self, line):
        parsed = self.__pattern.parseString(line)
        priority = int(parsed[0])

        return {
            "log_level": map_priority_to_log_level(priority),
            "service": parsed[1],
            "message": parsed[2].rstrip("\x00"),
        }


async def setup_syslog_server():
    parser = Parser()

    async def handler(connection):
        async for message in connection:
            parsed = parser.parse(bytes.decode(message.strip()))
            logger = getLogger(parsed["service"])
            logger.log(parsed["log_level"], parsed["message"])

    async with aioudp.serve("127.0.0.1", 11514, handler):
        while True:
            await sleep(1)
