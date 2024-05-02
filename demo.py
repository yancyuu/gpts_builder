from gpts_builder.builder.llm.llm_builder import LLM
from gpts_builder.builder.plugin.kb_builder import KbPluginBuilder

llm = LLM(model="gpt-3.5-turbo-16k")
llm.set_system("你是一个AI助理").set_prompt("你是谁").chat_completions()
