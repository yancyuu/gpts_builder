# GPTS Builder

GPTS Builder 是一个高度模块化的 Python 库，专为快速构建和部署基于大型语言模型（如 GPT-3 或 GPT-4）的应用而设计。它提供了一系列工具，使开发者能够轻松管理会话、创建提示词模板、构建对话流程，并进行配置管理。

## 特点

- **上下文管理器**：有效管理对话状态，支持多种存储模式。
- **提示词模板构建器**：快速生成和管理提示词模板，提高对话生成的效率和质量。
- **大模型对话构建器**：继承自提示词模板构建器，提供高效的对话管理。
- **配置管理器**：灵活配置模型参数，包括模型名称和最大 Token 数量。
- **存储模式支持**：支持全局变量和 Redis 存储，确保灵活性和扩展性。

## 架构概览

GPTS Builder 采用模块化设计，主要包括以下四个核心组件：

1. **上下文管理器**：管理用户会话和状态，支持全局变量和 Redis 存储模式。
2. **提示词模板构建器**：构建和维护用于生成模型提示词的模板。
3. **大模型对话构建器**：基于提示词模板生成对话，支持快速部署和测试模型应用。
4. **配置管理器**：中心化管理所有模型和应用配置。

## 开发计划

| 功能                           | 状态        |
| ------------------------------ | ----------- |
| 上下文管理器                   | ✅           |
| 提示词模板构建器               | ✅           |
| 大模型对话构建器               | ✅           |
| 配置管理器                     | ✅           |
| Redis 存储模式支持             | ✅           |
| 全局变量存储模式               | ✅           |
| 支持流式输出                   | ☐           |
| 知识库集成                     | ☐           |
| GPTS缓存                       | ☐           |

> 知识库集成：将提供与大型知识库的集成，增强模型的应答能力。
> GPTS缓存：为了提高响应速度和减少API调用成本，将实现请求结果的缓存机制。

### 大模型对话构建器

大模型对话构建器继承自提示词模板构建器，集成模板管理与对话生成的功能，支持复杂的对话流程控制，使得生成的对话更加自然和流畅。

#### 可用类：
- `LLM`: 大模型对话管理。
- `LLMAsync`:  异步大模型对话管理。

```python
from gpts_builder.builder import LLM
```

### 上下文管理器

上下文管理器负责维护对话状态，确保跨会话的数据持久化和状态管理。支持以下存储模式：

- **全局变量模式**：适用于单用户或不需持久化的简单应用。
- **Redis 存储模式**：适用于分布式应用和需要高可用性及可扩展性的企业级应用。

#### 可用类：

- `SessionManager`: 标准会话管理。
- `SessionManagerAsync`: 异步会话管理，适用于异步应用。
- `RedisStorage`: 为使用 Redis 提供的会话存储解决方案。
- `RedisStorageAsync`: 异步Redis存储实现。

```python
from gpts_builder.session_manager import SessionManager
from gpts_builder.session_manager import SessionManagerAsync
from gpts_builder.session_manager.storage.redis_storage import RedisStorage
from gpts_builder.session_manager.storage.redis_storage_async import RedisStorageAsync
```

### 插件构建器
提示词模板构建器允许开发者快速创建和管理用于生成模型提示的模板，极大地提高对话内容的生成效率和质量。

#### 可用类：
- `BasePluginBuilder`: 构建插件基类。
- `KbPluginBuilder`: 知识插件构建器。

```python
from gpts_builder.builder.plugin.base_builder import BasePluginBuilder
from gpts_builder.builder.plugin.kb_builder import KbPluginBuilder
```

### 配置管理器

配置管理器提供一个中心化的接口来管理所有相关配置，支持实时更新配置如模型选择和 Token 数量限制等，确保所有依赖组件能即时反映这些更改。


- `ConfigManager`:  配置管理。

```python
from gpts_builder.config import config_manager
```

## 安装

安装 GPTS Builder 非常简单，只需以下几步：

```bash
pip install gpts-builder
```
## 快速开始
以下是一个简单的示例，展示如何使用 GPTS Builder 来创建一个基于 GPT 模型的对话应用：

```python
Copy code
from gpts_builder.builder.llm.llm_builder import LLM
from gpts_builder.builder.plugin.kb_builder import KbPluginBuilder
from gpts_builder.config import config_manager

# 初始化配置

config_manager.base_url = "https://www.lazygpt.cn/api【改成你的大模型请求地址】"
config_manager.apikey = "写你的apikey"

# 初始化大模型对话构建器



llm = LLM(model="gpt-3.5-turbo")
llm.set_system("你是一个AI助理").set_prompt("测试回复").chat_completions()
```

## 贡献
欢迎通过 GitHub 提交 Pull Requests 或开 Issue 来贡献代码或提出功能请求。

## 许可证
本项目采用 MIT 许可证，详情请查阅 LICENSE 文件。

