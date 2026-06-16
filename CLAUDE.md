## 项目说明
基于 Python 3.9+ 的 pytest 自动化测试框架，集成 HTML 图形化报告。
目标：编写可复用的测试基础设施，让测试人员只需关注用例逻辑。

## 技术栈
- Python 3.9+
- pytest 8.x（测试框架）
- pytest-html（HTML 图形化报告）
- requests（HTTP 客户端）

## 目录规范
- config/       — 全局配置，不可放业务逻辑
- testcases/    — 测试用例，一个模块一个业务领域
- utils/        — 工具层，可复用的 HTTP 客户端、日志等
- reports/      — 测试报告输出，不提交 git
- conftest.py   — pytest 全局 fixtures 和 hooks

## 约束
- 所有 HTTP 调用通过 utils/http_client 发起，禁止在用例中直接 import requests
- 新加测试用例只需在 testcases/ 下新建 .py 文件，写 def test_xxx 即可自动发现
- 报告要求每个 case 展开后能看到请求/响应详情
