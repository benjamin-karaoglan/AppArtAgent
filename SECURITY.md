# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email us at:

📧 **benjamin.karaoglan@appartagent.com**

### What to Include

Please include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Impact**: Potential impact and severity assessment
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected
- **Suggested Fix**: If you have a suggested fix or mitigation

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

### Disclosure Policy

- We will acknowledge receipt of your report within 48 hours
- We will provide regular updates on the progress
- We will notify you when the issue is fixed
- We request that you do not publicly disclose the issue until we have addressed it
- We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Best Practices

When deploying AppArt Agent:

### Environment Variables

- Never commit `.env` files to version control
- Use secrets management (e.g., GCP Secret Manager) in production
- Rotate API keys regularly
- Use strong, unique `SECRET_KEY` values

### Database

- Use strong passwords for database connections
- Enable SSL/TLS for database connections in production
- Regularly backup database data
- Restrict database network access

### API Security

- Keep dependencies updated
- Enable CORS only for trusted origins
- Use HTTPS in production
- Implement rate limiting

### Storage

- Use presigned URLs with short expiration times
- Implement proper access controls on storage buckets
- Never expose storage credentials in frontend code

## Security Updates

Security updates will be released as patch versions. We recommend:

1. Subscribing to GitHub releases for notifications
2. Regularly updating to the latest patch version
3. Following our security advisories

## Acknowledgments

We appreciate the security research community's efforts in helping keep AppArt Agent secure. Responsible disclosure helps protect our users.

Thank you for helping make AppArt Agent more secure!
