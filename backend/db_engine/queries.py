"""Global SQL constants used by the plan-management report."""

PLAN_QUERY = """
    SELECT p.id AS plan_id,
           p.document_provider AS dp,
           p.user_group_id AS tpa,
           s.plan_record_type,
           p.created_on
    FROM plan p
    LEFT JOIN plan_setup s ON s.plan_id = p.id
    WHERE p.is_active = TRUE
"""

PLAN_STATUS_QUERY = """
    SELECT p.user_group_id AS tpa,
           p.id AS plan_id,
           p.additional_info->>'PriorDocumentProvider' AS prior_dp,
           s.plan_record_type,
           st.name AS stage,
           st.status AS plan_status,
           st.last_updated_at
    FROM plan p
    LEFT JOIN plan_setup s ON s.plan_id = p.id
    JOIN stage st ON st.plan_id = p.id
    WHERE p.is_active = TRUE
"""
