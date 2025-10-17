from enum import StrEnum

class LLMProvider(StrEnum):
    GOOGLE = "google"
    OPENAI = "openai"

class LLMModels(StrEnum):
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class AgentTable(StrEnum):
    INJECTOR = "injections"
    VALIDATOR = "validations"
    RESEARCHER = "researches"
    CONDENSER = "condenser"