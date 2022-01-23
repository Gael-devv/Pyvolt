from typing import List, NewType

Snowflake = NewType("_id", str)
SnowflakeList = List[Snowflake]
