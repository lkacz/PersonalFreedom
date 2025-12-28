# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Personal Freedom, please follow these steps:

### Do NOT

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Do

1. **Email**: Send details to the repository owner via GitHub private message
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Status Update**: Within 7 days with our assessment
- **Resolution**: Security patches are prioritized and typically released within 30 days

### Security Considerations

This application modifies the Windows hosts file, which requires administrator privileges. Key security measures implemented:

1. **Password Protection**: Strict mode passwords are hashed using bcrypt with salts
2. **Input Validation**: All hostname inputs are validated before being written to hosts file
3. **Marker-Based Isolation**: Application entries are clearly marked and isolated in the hosts file
4. **No Network Communication**: The app operates entirely locally with no external data transmission

### Scope

The following are in scope for security reports:

- Bypass of strict mode password protection
- Arbitrary file write vulnerabilities
- Code injection through site input fields
- Privilege escalation issues
- Data exposure of sensitive information

### Out of Scope

- Denial of service through normal usage
- Issues requiring physical access to the machine
- Social engineering attacks
- Issues in third-party dependencies (report to upstream)

## Security Best Practices for Users

1. **Keep Updated**: Always use the latest version
2. **Strong Passwords**: Use a strong password for strict mode
3. **Admin Access**: Only grant admin privileges when starting focus sessions
4. **Backup Config**: Regularly backup your configuration before updates

Thank you for helping keep Personal Freedom secure!
