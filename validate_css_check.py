from app import CSS_TEMPLATE

assert '<style>' in CSS_TEMPLATE, 'style tag missing'
assert '__FONT_IMPORT__' in CSS_TEMPLATE, 'placeholder missing'
assert CSS_TEMPLATE.index('<style>') < CSS_TEMPLATE.index('__FONT_IMPORT__'), 'placeholder is before style tag'
assert CSS_TEMPLATE.index('__FONT_IMPORT__') < CSS_TEMPLATE.index(':root'), 'placeholder is outside the root styles'
print('CSS validation passed: font import token is nested inside the style block.')
