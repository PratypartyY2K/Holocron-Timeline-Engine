from enum import StrEnum


class NodeType(StrEnum):
    EVENT = "event"
    CHARACTER = "character"
    PLANET = "planet"
    FACTION = "faction"


class RelationshipType(StrEnum):
    CAUSES = "CAUSES"
    INVOLVES = "INVOLVES"
    LOCATED_IN = "LOCATED_IN"
    MEMBER_OF = "MEMBER_OF"
    ALLIED_WITH = "ALLIED_WITH"
    ENEMY_OF = "ENEMY_OF"

