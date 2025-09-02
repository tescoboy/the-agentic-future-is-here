# Documentation Index

Welcome to the AdCP Demo documentation! This index provides quick access to all project documentation, with a focus on the **CI/CD pipeline** and **development standards**.

## 🚀 **CI/CD Pipeline Documentation**

### **Essential Reading (Start Here)**
- **[CI/CD Setup Guide](CI_CD_SETUP.md)** - Complete setup and usage guide
- **[Implementation Summary](../CI_CD_IMPLEMENTATION_SUMMARY.md)** - What was built and why
- **[Project Rules](PROJECT_RULES.md)** - Mandatory rules enforced by CI/CD

### **Development Standards**
- **[Development Standards](DEVELOPMENT_STANDARDS.md)** - Code quality and structure standards
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 📚 **Documentation Categories**

### **Getting Started**
- **[README](../README.md)** - Project overview and quick start
- **[CI/CD Setup Guide](CI_CD_SETUP.md)** - Setup development environment
- **[Implementation Summary](../CI_CD_IMPLEMENTATION_SUMMARY.md)** - What was implemented

### **Development Process**
- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution workflow and standards
- **[Development Standards](DEVELOPMENT_STANDARDS.md)** - Code quality requirements
- **[Project Rules](PROJECT_RULES.md)** - Mandatory project rules

### **Technical Documentation**
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[MCP Documentation](MCP.md)** - Model Context Protocol implementation
- **[Agents Documentation](AGENTS.md)** - Agent configuration and usage
- **[Grounding Documentation](grounding.md)** - Web context grounding features

### **Configuration and Tools**
- **[Makefile](../Makefile)** - Available commands and targets
- **[pyproject.toml](../pyproject.toml)** - Pytest and project configuration
- **[Requirements Files](../requirements.txt)** - Python dependencies

## 🔧 **Quick Reference**

### **CI/CD Commands**
```bash
# Check pipeline status
./scripts/ci-status.sh

# Setup development environment
./scripts/setup-ci.sh

# Run full CI pipeline locally
./scripts/run-ci-local.sh

# Use Makefile commands
make help
```

### **Quality Checks**
```bash
# Run all quality checks
make pre-commit

# Format code
make fmt

# Run tests with coverage
make test-coverage

# Security checks
make security
```

### **Test Commands**
```bash
# Run specific test types
make test-unit        # Unit tests
make test-integration # Integration tests
make test-rag         # RAG functionality
make test-mcp         # MCP protocol
make test-web         # Web grounding
```

## 📋 **Documentation Standards**

### **Required Reading for Contributors**
1. **[Project Rules](PROJECT_RULES.md)** - Understand mandatory requirements
2. **[Development Standards](DEVELOPMENT_STANDARDS.md)** - Learn code quality standards
3. **[Contributing Guide](../CONTRIBUTING.md)** - Follow contribution process
4. **[CI/CD Setup Guide](CI_CD_SETUP.md)** - Setup development environment

### **Required Reading for Maintainers**
1. **[Project Rules](PROJECT_RULES.md)** - Enforce mandatory requirements
2. **[Development Standards](DEVELOPMENT_STANDARDS.md)** - Maintain code quality
3. **[CI/CD Setup Guide](CI_CD_SETUP.md)** - Understand pipeline operation
4. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Resolve common issues

## 🎯 **Documentation Goals**

### **For Developers**
- **Clear standards** for code quality
- **Step-by-step guides** for common tasks
- **Examples and templates** for best practices
- **Troubleshooting help** for common issues

### **For Maintainers**
- **Enforcement mechanisms** for quality standards
- **Review processes** and checklists
- **Pipeline configuration** and maintenance
- **Team onboarding** and training

### **For the Project**
- **Consistent quality** across all contributions
- **Maintainable code** that can be safely refactored
- **Professional development** practices
- **Scalable team** processes

## 📊 **Documentation Quality**

### **Standards**
- **Accuracy**: All information must be current and correct
- **Clarity**: Instructions must be clear and actionable
- **Completeness**: Cover all necessary topics and edge cases
- **Consistency**: Use consistent formatting and terminology

### **Maintenance**
- **Regular updates** when features change
- **Version control** for all documentation
- **Review process** for accuracy and clarity
- **Feedback collection** from users

## 🔍 **Finding Information**

### **By Topic**
- **CI/CD Pipeline**: [CI/CD Setup Guide](CI_CD_SETUP.md)
- **Code Quality**: [Development Standards](DEVELOPMENT_STANDARDS.md)
- **Contributing**: [Contributing Guide](../CONTRIBUTING.md)
- **Troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)

### **By Audience**
- **New Contributors**: Start with [Project Rules](PROJECT_RULES.md)
- **Developers**: Focus on [Development Standards](DEVELOPMENT_STANDARDS.md)
- **Maintainers**: Review [CI/CD Setup Guide](CI_CD_SETUP.md)
- **Users**: Check [README](../README.md) and [Troubleshooting Guide](TROUBLESHOOTING.md)

### **By Task**
- **Setup Environment**: [CI/CD Setup Guide](CI_CD_SETUP.md)
- **Run Tests**: [Development Standards](DEVELOPMENT_STANDARDS.md)
- **Submit Code**: [Contributing Guide](../CONTRIBUTING.md)
- **Fix Issues**: [Troubleshooting Guide](TROUBLESHOOTING.md)

## 📞 **Getting Help**

### **Documentation Issues**
1. **Check this index** for relevant documents
2. **Search existing documentation** for your topic
3. **Review related documents** for context
4. **Ask maintainers** for clarification

### **Missing Information**
1. **Identify the gap** in documentation
2. **Check if it's covered elsewhere**
3. **Propose documentation addition**
4. **Submit pull request** with new content

### **Improvement Suggestions**
1. **Identify the issue** with current documentation
2. **Propose specific improvements**
3. **Submit issue or pull request**
4. **Work with maintainers** on implementation

## 🔄 **Documentation Updates**

### **When to Update**
- **New features** added to the project
- **Process changes** in development workflow
- **Tool updates** or configuration changes
- **Bug fixes** that affect documentation
- **User feedback** indicates improvements needed

### **Update Process**
1. **Identify the need** for documentation update
2. **Make the changes** in a feature branch
3. **Test the documentation** for accuracy
4. **Submit pull request** with changes
5. **Review and merge** after approval

---

## 📋 **Quick Start Checklist**

For new contributors, follow this checklist:

- [ ] **Read [Project Rules](PROJECT_RULES.md)** - Understand mandatory requirements
- [ ] **Read [Development Standards](DEVELOPMENT_STANDARDS.md)** - Learn code quality standards
- [ ] **Read [Contributing Guide](../CONTRIBUTING.md)** - Follow contribution process
- [ ] **Setup environment** using [CI/CD Setup Guide](CI_CD_SETUP.md)
- [ ] **Run quality checks** using `make pre-commit`
- [ ] **Run tests** using `make test-coverage`
- [ ] **Start contributing** following established standards

**Remember**: The CI/CD pipeline enforces all quality standards. Code that doesn't meet the standards will not be merged. Always run quality checks locally before pushing.

Welcome to AdCP Demo! 🚀

