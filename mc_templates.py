# -*- coding: utf-8 -*-
"""
마인크래프트 제작 도우미용 템플릿/프리셋 모음.
코드가 길어지는 것을 막기 위해 상수 데이터를 분리.
"""

CHALLENGE_POOL = [
    "네더에서만 생존 10분",
    "눈덩이로만 엔더맨 처치",
    "인벤토리 9칸 제한",
    "채광 금지, 상자 루팅만 허용",
    "파밍 없이 보스 도전",
    "한 블록마다 점프 필수",
    "스니크 금지 챌린지",
    "점수판으로 시청자 미션 카운트",
    "동굴에서만 건축",
    "동물 친구와 동행 필수",
    "야간만 활동",
    "랜덤 효과 30초마다 적용",
    "낙사 금지, 고지대 이동",
    "아이템 버리기 금지",
    "밥 없이 포만도 회복 금지",
    "철 장비 금지, 바로 다이아 도전",
    "포션 없이 엔더 드래곤",
]

FUNCTION_SNIPPETS = {
    "tick_timer": "# 매 틱마다 1씩 증가\nscoreboard players add #tick timer 1\n",
    "welcome": 'tellraw @a {"text":"서버에 오신 것을 환영합니다!","color":"gold"}\n',
    "boss_bar": "bossbar add my:progress \"진행률\"\nbossbar set my:progress max 100\nbossbar set my:progress players @a\n",
    "advancement_grant": "advancement grant @a everything\n",
    "loop_sound": "playsound minecraft:block.note_block.pling master @a ~ ~ ~ 1 1\n",
}

ADVANCEMENT_SAMPLE = {
    "display": {
        "title": {"text": "첫 다이아", "color": "aqua"},
        "description": {"text": "다이아몬드를 획득하세요"},
        "icon": {"item": "minecraft:diamond"},
        "frame": "task",
        "show_toast": True,
        "announce_to_chat": True,
        "hidden": False,
    },
    "criteria": {
        "obtain_diamond": {
            "trigger": "minecraft:inventory_changed",
            "conditions": {"items": [{"items": ["minecraft:diamond"]}]},
        }
    },
    "rewards": {"experience": 50},
}

PREDICATE_SAMPLE = {
    "condition": "minecraft:entity_properties",
    "entity": "this",
    "predicate": {"equipment": {"mainhand": {"items": ["minecraft:diamond_sword"]}}},
}

PACK_FORMATS = {
    "1.21.x 데이터팩": 48,
    "1.21.x 리소스팩": 34,
    "1.20.6 데이터팩": 41,
    "1.20.6 리소스팩": 34,
}

__all__ = [
    "CHALLENGE_POOL",
    "FUNCTION_SNIPPETS",
    "ADVANCEMENT_SAMPLE",
    "PREDICATE_SAMPLE",
    "PACK_FORMATS",
]
