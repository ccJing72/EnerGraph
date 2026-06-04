# EnerGraph — Phase 5: 语音助手

**目标**: 在 API 层添加语音输入/输出，前端可选接入，实现语音问答全链路。  
**前置条件**: Phase 2 完成（FastAPI 可用）  
**完成标志**: 语音输入转文字 → Agent 回答 → 文字转语音，Streamlit 前端可用

---

## 业务场景

### 场景 1: 语音输入
运维工程师在机房巡检时，通过平板对 Agent 说："冷水机房现在 COP 多少？"

系统应：
1. 录音 → 调用 Whisper STT → 转为文字
2. 文字自动填入 chat_input，走正常 Agent 流程
3. 流式返回回答

### 场景 2: 语音输出
用户点击"朗读"按钮，系统将 Agent 回答朗读出来，方便用户在嘈杂环境中听取报告。

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/skills/voice_skill.py` | 语音 Skill：封装 STT/TTS 调用逻辑，独立于其他 Skill |
| `src/tests/test_voice.py` | mock Whisper/TTS，测试端点请求/响应格式 |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/services/api.py` | 新增 `POST /voice/transcribe` + `POST /voice/speak` |
| `src/frontend/app.py` | 录音按钮 + 朗读按钮 |

---

## 子任务（每个子任务 = 一个 commit）

### T1: STT 端点（语音转文字）
- **文件**: `src/services/api.py`
- **改动**:
  - 新增 `POST /voice/transcribe`
  - 接收 `multipart/form-data`，字段 `audio: UploadFile`（支持 wav/mp3/webm）
  - 调用 OpenAI Whisper API（或本地 whisper 模型）转文字
  - 返回 `{"text": "冷水机房现在COP多少", "language": "zh"}`
  - 音频大小限制：最大 10MB，超过返回 413
- **验收**: `curl -X POST localhost:8000/voice/transcribe -F "audio=@test.wav"` 返回 `{"text": "..."}`

### T2: TTS 端点（文字转语音）
- **文件**: `src/services/api.py`
- **改动**:
  - 新增 `POST /voice/speak`
  - 接收 `{"text": "...", "voice": "alloy"}`（voice 可选：alloy/echo/fable/onyx/nova/shimmer）
  - 调用 OpenAI TTS API，返回 `audio/mpeg` 流
  - 文字长度限制：最大 4096 字符
  - 若 `OPENAI_API_KEY` 未配置，返回 501 + 提示信息
- **验收**: `curl -X POST localhost:8000/voice/speak -d '{"text":"你好"}' -H "Content-Type: application/json"` 返回可播放 mp3

### T3: Streamlit 语音输入
- **文件**: `src/frontend/app.py`
- **改动**:
  - 使用 `streamlit-audiorecorder` 组件添加录音按钮
  - 录音完成后自动调用 `/voice/transcribe`
  - 转写结果填入 `st.chat_input`
  - 显示录音状态（正在录音 / 转写中 / 完成）
- **依赖**: `pip install streamlit-audiorecorder`
- **验收**: 点击录音 → 说话 → 文字自动填入输入框

### T4: Streamlit 语音输出
- **文件**: `src/frontend/app.py`
- **改动**:
  - 回答生成后，在答案下方显示"朗读"按钮
  - 点击后调用 `/voice/speak`，返回 `st.audio()` 组件
  - 朗读期间按钮变为"停止"
- **验收**: 点击朗读可听到报告朗读，可停止

### T5: VoiceSkill 骨架 + 测试
- **文件**: `src/skills/voice_skill.py`, `src/tests/test_voice.py`
- **改动**:
  - 新建 `voice_skill.py`，继承 BaseSkill（若已完成），声明：
    - `name = "voice"`
    - `tools = []`（语音端点不经过工具层，直接调用外部 API）
    - `description = "语音输入/输出（STT + TTS）"`
  - `test_voice.py`：mock OpenAI API，测试 STT/TTS 端点请求/响应格式
  - 测试音频大小超限返回 413
  - 测试 OPENAI_API_KEY 未配置时 TTS 返回 501
- **验收**: `pytest src/tests/test_voice.py` 全部通过

---

## 关键架构决策

**为什么 STT/TTS 放在 API 层而非 Graph 节点？**  
语音是前端交互层能力，不参与 Agent 推理流程。将语音转文字后注入正常的 Agent 流程，保持 Graph 简洁。语音输出是后处理，在回答生成后触发。

**为什么用 OpenAI Whisper 而非本地模型？**  
Whisper API 零部署、高精度、支持多语言。若后续对延迟/隐私有要求，可替换为本地 whisper.cpp（模型文件 ~1GB），接口签名不变。

**为什么单独建 VoiceSkill 而非集成到 UIRouterSkill？**  
语音是独立能力维度，与监控查询无关。单独 Skill 保证职责单一，未来可独立禁用（如客户不需要语音时直接不注册）。

---

## 依赖安装
```bash
pip install openai                        # Whisper STT + TTS
pip install streamlit-audiorecorder       # Streamlit 录音组件
```

## 关键文件
- `src/services/api.py` — STT/TTS 端点
- `src/skills/voice_skill.py` — 语音 Skill（独立）
- `src/frontend/app.py` — 录音/朗读 UI

## Skills 融合说明
- T1-T2 语音端点实现后，新建 `src/skills/voice_skill.py`（完全独立，不影响其他 Skill）
- 若 BaseSkill 方案已完成，继承之；否则暂用现有 Skill 骨架
- 详见 `docs/plan_skills_refactor.md`
