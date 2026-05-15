from aion.thread_audit import ThreadSafetyAudit, audit_running_threads


class TestThreadAudit:
    def test_audit_clean_module(self):
        auditor = ThreadSafetyAudit()
        import aion.eventbus as mod
        findings = auditor.audit_module(mod)
        assert isinstance(findings, list)

    def test_audit_running_threads(self):
        threads = audit_running_threads()
        assert isinstance(threads, list)
        if threads:
            assert "name" in threads[0]
            assert "daemon" in threads[0]
            assert "alive" in threads[0]

    def test_report_format(self):
        auditor = ThreadSafetyAudit()
        import aion.eventbus as mod
        auditor.audit_module(mod)
        report = auditor.report()
        assert isinstance(report, str)
        assert len(report) > 0
