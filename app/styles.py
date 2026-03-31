"""Shared CSS for the Frederick Platform."""

GLOBAL_CSS = """
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: white; border-radius: 1rem; padding: 1.25rem;
        border: 1px solid #e2e8f0; margin-bottom: 0.5rem;
    }
    .metric-card h4 { color: #64748b; font-size: 0.85rem; margin: 0 0 0.5rem 0; font-weight: 500; }
    .metric-card .value { font-size: 1.5rem; font-weight: 600; color: #0f172a; }
    .metric-card .change-up { font-size: 0.75rem; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 9999px; }
    .metric-card .change-down { font-size: 0.75rem; color: #dc2626; background: #fee2e2; padding: 2px 8px; border-radius: 9999px; }
    .activity-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 1rem; background: #f8fafc; border-radius: 0.75rem; margin-bottom: 0.35rem;
    }
    .badge-success, .badge-completed, .badge-high, .badge-done { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-warning, .badge-reviewing, .badge-medium { font-size: 0.65rem; background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-error, .badge-failed { font-size: 0.65rem; background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-pending, .badge-low { font-size: 0.65rem; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-running { font-size: 0.65rem; background: #dbeafe; color: #2563eb; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .quick-stat { background: white; border-radius: 0.5rem; padding: 0.6rem 0.75rem; }
    .quick-stat .label { font-size: 0.8rem; color: #64748b; }
    .quick-stat .val { font-size: 1.2rem; font-weight: 600; color: #0f172a; }
    .quick-stat .sub { font-size: 0.65rem; color: #64748b; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1rem 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
"""
