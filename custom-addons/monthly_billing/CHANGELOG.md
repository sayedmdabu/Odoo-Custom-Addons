# Changelog

All notable changes to the Monthly Billing module will be documented in this file.

## [18.0.1.0.0] - 2025-01-01

### Added
- Initial release for Odoo 18 Community Edition
- Monthly billing header model with full field set
- Monthly billing line model for invoice aggregation
- Generation wizard with period calculation logic
- Support for end-of-month and specific day closing
- Professional QWeb PDF report template
- Bilingual support (Japanese/English)
- Multi-company support with record rules
- Security groups (User and Manager)
- State management workflow (Draft → Confirmed → Done → Cancel)
- Preview functionality before generation
- Customer extension with monthly billing settings
- Smart buttons for related records
- Comprehensive search and filter options
- Access control list for all models
- Sequence generation for billing numbers
- Full i18n support with Japanese translations

### Features
- Flexible closing date configuration (1-31, where 31 = end of month)
- Automatic period calculation based on closing logic
- Batch creation for performance optimization
- Invoice state filtering (posted only / including draft)
- Customer selection for targeted generation
- Dry run mode for testing
- PDF output tracking
- Chatter integration for collaboration
- Activity tracking
- Monetary field support with currency
- Tax calculation integration
- Product reference in lines
- Original invoice tracking
- Comprehensive reporting with bilingual headers
- Payment information display
- Contact information in reports

### Technical Details
- Compatible with Odoo 18 CE and EE
- Uses only CE standard features
- Follows Odoo best practices
- Optimized for large data volumes
- Multi-language ready
- Upgrade-safe implementation
- Minimal standard overrides

### Documentation
- Complete README with usage instructions
- Installation guide with verification steps
- Module description for apps page
- Inline code documentation
- Japanese translation file
- Quick test scenario included

## Future Enhancements (Planned)

### Version 18.0.2.0.0 (Planned)
- Previous balance / current payment tracking
- Group billing consolidation
- CSV/Excel export functionality
- Email auto-send feature
- Advanced filtering options
- Bulk operations support
- Additional closing type presets
- Enhanced preview with detailed breakdown

### Version 18.0.3.0.0 (Planned)
- Bank transfer file generation (Zengin format)
- Payment reconciliation integration
- Recurring billing templates
- Approval workflow
- Custom report templates
- Dashboard analytics
- API endpoints for integration
- Mobile-optimized views

---

## Version Numbering

This module follows semantic versioning: `[ODOO_VERSION].[MAJOR].[MINOR].[PATCH]`

- **ODOO_VERSION**: Odoo version (18.0)
- **MAJOR**: Major version (breaking changes)
- **MINOR**: Minor version (new features, backward compatible)
- **PATCH**: Patch version (bug fixes)

## Support

For issues, feature requests, or contributions, please contact the module maintainer.
