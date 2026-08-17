TRANSLATIONS = {
    "zh-CN": {
        "app_name": "LLM 工程学习台", "dashboard": "学习总览", "curriculum": "课程", "thoughts": "思考笔记",
        "resources": "外部链接", "progress": "进度", "language": "语言", "overall_progress": "总体进度",
        "completed_lessons": "已完成课程", "thought_count": "思考记录", "resource_count": "收藏链接",
        "recent_thoughts": "最近思考", "recent_resources": "最近链接", "add_thought": "记录思考", "add_resource": "添加链接",
        "edit": "编辑", "delete": "删除", "save": "保存", "cancel": "取消", "title": "标题", "content": "内容",
        "description": "备注", "tags": "标签", "related_lesson": "关联课程", "unassigned": "不关联课程", "status": "状态",
        "not_started": "未开始", "in_progress": "学习中", "completed": "已完成", "score": "测试得分", "source": "课程来源",
        "empty_thoughts": "还没有思考记录。学习过程中遇到观点、疑问和结论，都可以记在这里。",
        "empty_resources": "还没有外部链接。可以保存论文、教程、博客、视频或 GitHub 项目。",
        "markdown_hint": "支持 Markdown，可记录自己的理解、疑问、代码片段和复盘。", "url": "URL", "open_link": "打开链接",
        "all_lessons": "全部课程", "backup": "导出备份", "learning_status": "学习状态"
    },
    "en": {
        "app_name": "LLM Engineering Learning", "dashboard": "Dashboard", "curriculum": "Curriculum", "thoughts": "Thoughts",
        "resources": "External Links", "progress": "Progress", "language": "Language", "overall_progress": "Overall progress",
        "completed_lessons": "Completed lessons", "thought_count": "Thoughts", "resource_count": "Saved links",
        "recent_thoughts": "Recent thoughts", "recent_resources": "Recent links", "add_thought": "Add thought", "add_resource": "Add link",
        "edit": "Edit", "delete": "Delete", "save": "Save", "cancel": "Cancel", "title": "Title", "content": "Content",
        "description": "Notes", "tags": "Tags", "related_lesson": "Related lesson", "unassigned": "No lesson", "status": "Status",
        "not_started": "Not started", "in_progress": "In progress", "completed": "Completed", "score": "Test score", "source": "Course source",
        "empty_thoughts": "No thoughts yet. Capture questions, conclusions, ideas, and reflections as you learn.",
        "empty_resources": "No external links yet. Save papers, tutorials, videos, blogs, or GitHub projects here.",
        "markdown_hint": "Markdown supported. Capture explanations, questions, code snippets, and retrospectives.", "url": "URL", "open_link": "Open link",
        "all_lessons": "All lessons", "backup": "Export backup", "learning_status": "Learning status"
    },
}

def normalize_lang(lang: str | None) -> str:
    return "en" if lang == "en" else "zh-CN"

def tr(lang: str, key: str) -> str:
    return TRANSLATIONS[normalize_lang(lang)].get(key, key)
