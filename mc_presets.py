# -*- coding: utf-8 -*-
"""
자주 쓰는 방송/녹화용 커맨드 프로파일 모음.
UI에서 선택 후 명령어 리스트를 출력/복사하도록 사용한다.
"""

PROFILES = {
    "녹화 기본": [
        "gamerule sendCommandFeedback false",
        "gamerule showDeathMessages true",
        "gamerule spectatorsGenerateChunks false",
        "gamerule doImmediateRespawn false",
        "time set day",
        "weather clear 999999",
        "title @a times 10 60 20",
    ],
    "스트림 라이트": [
        "gamerule keepInventory true",
        "gamerule doDaylightCycle false",
        "gamerule doWeatherCycle false",
        "gamerule reducedDebugInfo true",
        "gamerule playersSleepingPercentage 0",
        "effect give @a night_vision 999999 0 true",
        "effect give @a saturation 5 0 true",
    ],
    "하드코어 챌린지": [
        "difficulty hard",
        "gamerule keepInventory false",
        "gamerule naturalRegeneration false",
        "gamerule doInsomnia true",
        "gamerule doImmediateRespawn false",
        "effect clear @a",
        "title @a title {\"text\":\"하드코어 시작!\",\"color\":\"red\"}",
    ],
    "테스트/디버그": [
        "gamerule logAdminCommands true",
        "gamerule commandBlockOutput true",
        "gamerule spectatorsGenerateChunks true",
        "gamerule sendCommandFeedback true",
        "gamerule reducedDebugInfo false",
    ],
}

__all__ = ["PROFILES"]
