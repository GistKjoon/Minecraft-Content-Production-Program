# -*- coding: utf-8 -*-
"""
오프라인 짧은 도움말/베스트 프랙티스 모음.
UI에서 항목을 선택해 설명을 보여준다.
"""

DOCS = {
    "점수판 설계": (
        "objective는 기능별로 분리하고 네임스페이스 느낌의 접두사를 사용하세요.\n"
        "예) game.timer, game.kill, ui.bossbar. 불필요한 setdisplay 남발을 피하고,\n"
        "필요할 때만 sidebar를 바꿔 깜빡임을 줄입니다."
    ),
    "명령 퍼포먼스": (
        "tick 함수에서 불필요한 반복 명령을 최소화하세요. 조건부 실행(execute if)\n"
        "로 대상을 좁히고, 점수 조건이 변할 때만 실행되도록 구조화하면 TPS를 보호할 수 있습니다."
    ),
    "리소스팩 구조": (
        "assets/<namespace>/textures, models, lang를 분리하고, pack.mcmeta의 pack_format을\n"
        "게임 버전에 맞게 지정하세요. 테스트용 텍스처는 이름에 _debug 등을 붙여 관리하면 좋습니다."
    ),
    "데이터팩 배포": (
        "datapacks/<name> 폴더를 그대로 zip으로 묶어 배포합니다. pack.mcmeta, data/minecraft/tags/functions\n"
        "의 load/tick 포함 여부를 확인하고, readme.txt에 사용 방법을 적어두면 사용자 문의를 줄일 수 있습니다."
    ),
    "테스트 체크": (
        "1) /reload 후 에러 로그 없는지 확인\n2) /datapack list enabled로 로드 확인\n"
        "3) 주요 함수 단위로 /function <ns>:<fn> 테스트\n4) 서버라면 퍼미션/권한도 점검하세요."
    ),
    "NBT/데이터": (
        "커맨드에서 NBT를 직접 작성할 때는 중괄호/쉼표를 꼭 확인하고, tellraw 등 JSON은\n"
        "따옴표 이스케이프를 주의하세요. 복잡한 구조는 mcfunction 분리 또는 storage 사용을 고려합니다."
    ),
}

__all__ = ["DOCS"]
