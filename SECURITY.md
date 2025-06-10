# Security Policy

## Supported Versions

We provide security updates for the following versions of the Cerevox Python SDK:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in the Cerevox Python SDK, please report it to us as follows:

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Send an email to **security@cerevox.ai** with the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fixes (if any)
   - Your contact information

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Status Updates**: We will keep you informed of our progress throughout the process
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### Disclosure Policy

- We will work with you to understand and resolve the issue quickly
- We will coordinate the disclosure timeline with you
- We will credit you in our security advisory (unless you prefer to remain anonymous)
- We ask that you do not publicly disclose the vulnerability until we have had a chance to address it

### Security Best Practices

When using the Cerevox Python SDK:

1. **API Keys**: Never hardcode API keys in your source code
   - Use environment variables or secure configuration management
   - Rotate API keys regularly
   - Use the minimum required permissions

2. **Dependencies**: Keep dependencies up to date
   - Regularly update the SDK to the latest version
   - Monitor for security advisories in dependencies

3. **Data Handling**: Follow secure data practices
   - Validate all input data
   - Use HTTPS for all API communications
   - Handle sensitive documents appropriately

4. **Error Handling**: Be careful with error messages
   - Don't expose sensitive information in logs or error messages
   - Implement proper error handling for network failures

### Contact

For any security-related questions or concerns:

- **Security Email**: security@cerevox.ai
- **General Support**: support@cerevox.ai
- **Website**: https://cerevox.ai

Thank you for helping us keep the Cerevox Python SDK secure! 