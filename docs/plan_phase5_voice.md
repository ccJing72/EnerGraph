# EnerGraph — Phase 5: 语音助手

**目标**: 在 API 层添加语音输入/输出，前端可选接入。
**前置条件**: Phase 2 完成（FastAPI 可用）
**完成标志**: 语音输入转文字 → Agent 回答 → 文字转语音，全链路可用

---

## 子任务（每个子任务 = 一个 commit）

### T1: STT 端点（语音转文字）
- **文件**: `src/services/api.py`
- **改动**: `POST /voice/transcribe`，接收音频文件，调用 Whisper API 返回文字
- **验收**: curl 上传 wav 文件返回 `{"text": "..."}`

### T2: TTS 端点（文字转语音）
- **文件**: `src/services/api.py`
- **改动**: `POST /voice/speak`，接收文字，返回 mp3 音频流
- **验收**: curl 返回可播放音频

### T3: Streamlit 语音输入
- **文件**: `src/frontend/app.py`
- **改动**: 添加录音按钮，录音后调用 /voice/transcribe，结果填入 chat_input
- **依赖**: `pip install streamlit-audiorecorder`
- **验收**: 点击录音 → 说话 → 文字自动填入输入框

### T4: Streamlit 语音输出
- **文件**: `src/frontend/app.py`
- **改动**: 报告生成后显示"播放"按钮，调用 /voice/speak 播放回答
- **验收**: 点击播放可听到报告朗读

### T5: 测试
- **文件**: `src/tests/test_voice.py`
- **改动**: mock Whisper/TTS，测试端点请求/响应格式
- **验收**: pytest 通过

---

## 关键文件
- `src/services/api.py` — STT/TTS 端点
- `src/frontend/app.py` — 录音/播放 UI

## 依赖
```bash
pip install openai  # Whisper STT + TTS（或替换为本地模型）
pip install streamlit-audiorecorder
```

## Skills 融合说明
- T1-T2 语音端点实现后，新增 `src/skills/voice_skill.py`（完全独立，不影响其他 Skill）
- 详见 `docs/plan_skills_refactor.md`
