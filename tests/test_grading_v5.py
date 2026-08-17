from app.current import app  # noqa: F401
from app.exam_system import short
from app.grading_v5 import contains_rubric_term, grade_question_strict


def test_short_technical_terms_require_boundaries():
    assert contains_rubric_term('Use RAG with MCP tools', 'rag')
    assert contains_rubric_term('Use RAG with MCP tools', 'mcp')
    assert not contains_rubric_term('storage layer', 'rag')
    assert not contains_rubric_term('xmcphelper', 'mcp')
    assert not contains_rubric_term('unsftuned model', 'sft')


def test_cjk_rubric_terms_keep_natural_substring_matching():
    assert contains_rubric_term('需要先做检索评测和证据检查', '检索')
    assert not contains_rubric_term('只调整界面样式', '检索')


def test_short_answer_does_not_award_false_positive_acronym_points():
    question = short(
        'strict-rubric-probe',
        '说明 RAG 与 MCP。',
        'Explain RAG and MCP.',
        (("rag", "检索增强"), ("mcp", "工具协议")),
        20,
    )
    false_positive = grade_question_strict(question, 'A storage service with xmcphelper identifiers.')
    correct = grade_question_strict(question, 'Use RAG for retrieval and MCP for tool connectivity.')
    assert false_positive['earned'] == 0
    assert correct['earned'] == 20
