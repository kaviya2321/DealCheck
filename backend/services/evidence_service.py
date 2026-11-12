import json
from typing import Dict, Any

def generate_evidence_html(deal_dict: Dict[str, Any]) -> str:
    """
    Generates a printable HTML/CSS evidence dossier for PayPal disputes or law enforcement reporting.
    """
    timeline = deal_dict.get("timeline", [])
    rules = deal_dict.get("rules_triggered", [])
    highlights = deal_dict.get("highlighted_phrases", [])

    timeline_rows = ""
    for ev in timeline:
        timeline_rows += f"""
        <div class="timeline-item">
            <div class="timeline-time">{ev.get('timestamp', '')}</div>
            <div class="timeline-title"><strong>{ev.get('title', '')}</strong> ({ev.get('type', '')})</div>
            <div class="timeline-desc">{ev.get('description', '')}</div>
        </div>
        """

    rules_rows = ""
    for r in rules:
        rules_rows += f"""
        <li style="margin-bottom: 6px;">
            <strong>{r.get('name', '')}</strong> (+{r.get('points', 0)} pts): {r.get('explanation', '')}
        </li>
        """

    highlights_rows = ""
    for h in highlights:
        highlights_rows += f"""
        <span class="phrase-tag">"{h.get('phrase', '')}" (weight: {h.get('weight', 0)})</span>
        """

    verdict_color = "#dc2626" if deal_dict.get("verdict") == "HIGH" else (
        "#d97706" if deal_dict.get("verdict") == "MEDIUM" else "#16a34a"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DealCheck Evidence Dossier - {deal_dict.get('id')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 40px;
            color: #1e293b;
            background: #ffffff;
            line-height: 1.5;
        }}
        .header {{
            border-bottom: 2px solid #003087;
            padding-bottom: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 800;
            color: #003087;
            letter-spacing: -0.5px;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 14px;
            color: #ffffff;
            background-color: {verdict_color};
        }}
        .card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
            background: #f8fafc;
        }}
        h2 {{
            font-size: 16px;
            color: #0f172a;
            margin-top: 0;
            margin-bottom: 12px;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 6px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .value {{
            font-size: 15px;
            font-weight: 600;
            color: #0f172a;
        }}
        .transcript {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 250px;
            overflow-y: auto;
        }}
        .phrase-tag {{
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #f87171;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin: 2px 4px 2px 0;
            font-weight: 600;
        }}
        .timeline-item {{
            border-left: 2px solid #0070ba;
            padding-left: 12px;
            margin-bottom: 12px;
            position: relative;
        }}
        .timeline-time {{
            font-size: 11px;
            color: #64748b;
        }}
        .timeline-title {{
            font-size: 13px;
            color: #0f172a;
        }}
        .timeline-desc {{
            font-size: 12px;
            color: #334155;
        }}
        @media print {{
            body {{ margin: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo">DealCheck Security Report</div>
            <div style="font-size: 13px; color: #64748b;">PayPal AI Hackathon Dispute Dossier</div>
        </div>
        <div>
            <span class="badge">{deal_dict.get('verdict', 'LOW')} RISK ({deal_dict.get('risk_score', 0)}/100)</span>
        </div>
    </div>

    <div class="card grid">
        <div>
            <div class="label">Deal ID</div>
            <div class="value">{deal_dict.get('id')}</div>
            <div class="label" style="margin-top: 8px;">Date Created</div>
            <div class="value">{deal_dict.get('created_at')}</div>
        </div>
        <div>
            <div class="label">Item Name</div>
            <div class="value">{deal_dict.get('item_name')}</div>
            <div class="label" style="margin-top: 8px;">Agreed Price</div>
            <div class="value">${deal_dict.get('price', 0):.2f} {deal_dict.get('currency', 'USD')}</div>
        </div>
    </div>

    <div class="card">
        <h2>1. Transaction Risk Analysis</h2>
        <p><strong>DealCheck Risk Score:</strong> {deal_dict.get('risk_score')}/100 (Initial: {deal_dict.get('initial_risk_score')}/100)</p>
        <p><strong>Calibrated Model A Probability:</strong> {deal_dict.get('model_probability', 0)*100:.2f}%</p>
        <p><strong>Plain-Language Explanation:</strong> {deal_dict.get('explanation')}</p>
        
        <h3>Rule Violations Triggered</h3>
        <ul>
            {rules_rows if rules_rows else "<li>No deterministic fraud rules violated.</li>"}
        </ul>

        <h3>Top Risk Contributing Phrases (Model Coefficients)</h3>
        <div>
            {highlights_rows if highlights_rows else "<span>No suspicious phrase triggers.</span>"}
        </div>
    </div>

    <div class="card">
        <h2>2. PayPal Sandbox Order Audit Trail</h2>
        <div class="grid">
            <div>
                <div class="label">PayPal Order ID</div>
                <div class="value">{deal_dict.get('paypal_order_id') or 'Not generated'}</div>
                <div class="label" style="margin-top: 8px;">Order Status</div>
                <div class="value">{deal_dict.get('paypal_status')}</div>
            </div>
            <div>
                <div class="label">Capture ID</div>
                <div class="value">{deal_dict.get('paypal_capture_id') or 'Pending capture'}</div>
                <div class="label" style="margin-top: 8px;">Environment</div>
                <div class="value">PayPal Sandbox (REST API Orders v2)</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>3. Seller Behavioral Litmus Test</h2>
        <p><strong>Seller's Response to PayPal Link:</strong></p>
        <div class="transcript">{deal_dict.get('seller_reply_text') or 'No seller reply recorded.'}</div>
        <p style="margin-top: 10px;">
            <strong>Model B Classification:</strong> {deal_dict.get('seller_classification') or 'N/A'}<br/>
            <strong>Litmus Test Verdict:</strong> {deal_dict.get('seller_litmus_verdict') or 'PENDING'} (Risk adjustment: {deal_dict.get('seller_risk_delta', 0)} pts)
        </p>
    </div>

    <div class="card">
        <h2>4. Original Conversation Transcript</h2>
        <div class="transcript">{deal_dict.get('chat_text')}</div>
    </div>

    <div class="card">
        <h2>5. Verified Chronological Event Timeline</h2>
        {timeline_rows}
    </div>

    <div class="no-print" style="margin-top: 30px; text-align: center;">
        <button onclick="window.print()" style="padding: 10px 24px; background: #0070ba; color: white; border: none; border-radius: 6px; font-weight: 700; cursor: pointer;">
            Print / Save as PDF
        </button>
    </div>
</body>
</html>
"""
    return html
