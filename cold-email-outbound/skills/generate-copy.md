---
name: generate-copy
description: Render and preview email copy for a stream without sending. Spintax + signal-anchor + offer slotting. Use to QA copy + check content variation before a campaign.
---

# generate-copy

Renders the actual per-contact email bodies for a stream so you can review them.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import config, data_layer, copy_gen; \
tpl = copy_gen.parse_template(config.TEMPLATES_DIR / 'seller_cold_cs.md'); \
c = data_layer.load_tier_a('CS', limit=5); \
[print('---', x.display_name, '---\n', copy_gen.render(tpl['steps'][0]['body'], x, brand='CS')[0]) for x in c]"
```

## Knobs
- `signal=...` → slot a real signal anchor; omit → the signal line is removed (never faked)
- `test_offer="comparable_sales"` → swap the OOV CTA for an A/B offer
- `copy_gen.variation_ratio([...])` → confirm ≥50% content variation across the batch

## Templates live in `templates/` — edit them directly; they're plain markdown.
