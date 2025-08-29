# Invoicing

Invoices summarize monthly usage costs per tenant. Run
`scripts/generate_invoices.py` or the `billing_cli.py invoice` command to create
invoices for a given period.

Outputs are written under `.dr_rd/tenants/{org}/{workspace}/billing/`:
- `invoice_YYYY-MM.json`
- `invoice_YYYY-MM.csv`
- `invoice_YYYY-MM.html`

Amounts are computed from usage summaries after subtracting free tier credits
and applying markups and taxes from `config/billing.yaml`. The JSON form mirrors
`dr_rd.billing.models.Invoice`. CSV provides a simple line-item breakdown and the
HTML file is a lightweight printable view.
