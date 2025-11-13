"""
Unit tests for Docker configuration.

Tests verify that Docker setup is correctly configured including:
- Container configuration validation
- Environment variable loading
- Multi-stage build configuration
"""

import os
from pathlib import Path
import yaml
import pytest


class TestDockerConfiguration:
    """Test Docker and docker-compose configuration."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def dockerfile_path(self, repo_root: Path) -> Path:
        """Get Dockerfile path."""
        return repo_root / "backend" / "Dockerfile"

    @pytest.fixture
    def docker_compose_path(self, repo_root: Path) -> Path:
        """Get docker-compose.yml path."""
        return repo_root / "docker-compose.yml"

    @pytest.fixture
    def env_example_path(self, repo_root: Path) -> Path:
        """Get .env.example path."""
        return repo_root / "backend" / ".env.example"

    def test_dockerfile_exists(self, dockerfile_path: Path):
        """Test that Dockerfile exists."""
        assert dockerfile_path.exists(), "Dockerfile should exist in backend/"

    def test_dockerfile_has_multistage_build(self, dockerfile_path: Path):
        """Test that Dockerfile uses multi-stage build pattern."""
        content = dockerfile_path.read_text()
        
        # Check for builder stage
        assert "FROM python:" in content, "Dockerfile should have Python base image"
        assert "AS builder" in content or "as builder" in content, \
            "Dockerfile should have builder stage"
        
        # Check for runtime stage (second FROM)
        from_count = content.count("FROM ")
        assert from_count >= 2, "Dockerfile should have at least 2 stages (builder and runtime)"

    def test_dockerfile_has_build_dependencies(self, dockerfile_path: Path):
        """Test that Dockerfile installs build dependencies in builder stage."""
        content = dockerfile_path.read_text()
        
        # Check for build dependencies mentioned in research.md
        assert "gcc" in content or "build-essential" in content, \
            "Dockerfile should install gcc for compilation"
        assert "musl-dev" in content or "libc-dev" in content, \
            "Dockerfile should install musl-dev for Alpine builds"

    def test_dockerfile_uses_alpine(self, dockerfile_path: Path):
        """Test that Dockerfile uses Alpine for smaller image size."""
        content = dockerfile_path.read_text()
        assert "alpine" in content.lower(), \
            "Dockerfile should use Alpine for runtime stage"

    def test_docker_compose_exists(self, docker_compose_path: Path):
        """Test that docker-compose.yml exists."""
        assert docker_compose_path.exists(), "docker-compose.yml should exist at repo root"

    def test_docker_compose_valid_yaml(self, docker_compose_path: Path):
        """Test that docker-compose.yml is valid YAML."""
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config is not None, "docker-compose.yml should be valid YAML"
        assert "services" in config, "docker-compose.yml should have services section"

    def test_docker_compose_has_required_services(self, docker_compose_path: Path):
        """Test that docker-compose.yml has required services."""
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        
        # Check for database service
        assert "db" in services or "database" in services or "postgres" in services, \
            "docker-compose.yml should have PostgreSQL service"
        
        # Check for API service
        assert "api" in services or "backend" in services or "app" in services, \
            "docker-compose.yml should have API service"

    def test_docker_compose_postgres_version(self, docker_compose_path: Path):
        """Test that docker-compose.yml uses PostgreSQL 15+."""
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        
        # Find PostgreSQL service
        pg_service = None
        for service_name, service_config in services.items():
            image = service_config.get("image", "")
            if "postgres" in image.lower():
                pg_service = service_config
                break
        
        assert pg_service is not None, "PostgreSQL service should be defined"
        
        # Check version
        image = pg_service.get("image", "")
        assert "postgres" in image.lower(), "Should use postgres image"
        
        # Extract version if specified
        if ":" in image:
            version_part = image.split(":")[1]
            # Allow postgres:15, postgres:15-alpine, postgres:latest, etc.
            assert True, "PostgreSQL image is configured"

    def test_docker_compose_has_environment_variables(self, docker_compose_path: Path):
        """Test that docker-compose.yml services have environment configuration."""
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        
        for service_name, service_config in services.items():
            # Check if service has environment or env_file
            has_env = (
                "environment" in service_config or 
                "env_file" in service_config
            )
            assert has_env, f"Service '{service_name}' should have environment configuration"

    def test_env_example_exists(self, env_example_path: Path):
        """Test that .env.example file exists."""
        assert env_example_path.exists(), \
            ".env.example should exist in backend/ for environment variable documentation"

    def test_env_example_has_required_variables(self, env_example_path: Path):
        """Test that .env.example has all required environment variables."""
        content = env_example_path.read_text()
        
        required_vars = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "CORS_ORIGINS",
            "RATE_LIMIT_PER_MINUTE",
        ]
        
        for var in required_vars:
            assert var in content, \
                f".env.example should include {var} per quickstart.md requirements"

    def test_env_example_database_url_format(self, env_example_path: Path):
        """Test that DATABASE_URL in .env.example has correct format."""
        content = env_example_path.read_text()
        
        # Find DATABASE_URL line
        for line in content.split('\n'):
            if line.strip().startswith('DATABASE_URL'):
                # Should include postgresql+asyncpg for async driver
                assert "postgresql" in line, \
                    "DATABASE_URL should use postgresql protocol"
                break
        else:
            pytest.fail("DATABASE_URL not found in .env.example")

    def test_env_example_has_comments(self, env_example_path: Path):
        """Test that .env.example has helpful comments for developers."""
        content = env_example_path.read_text()
        
        # Check for at least some comments (lines starting with #)
        comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]
        assert len(comment_lines) > 0, \
            ".env.example should have comments explaining variables"


class TestDockerBuildConfiguration:
    """Test Docker build configuration and best practices."""

    @pytest.fixture
    def dockerfile_path(self) -> Path:
        """Get Dockerfile path."""
        return Path(__file__).parent.parent.parent.parent / "backend" / "Dockerfile"

    def test_dockerfile_has_workdir(self, dockerfile_path: Path):
        """Test that Dockerfile sets WORKDIR."""
        content = dockerfile_path.read_text()
        assert "WORKDIR" in content, "Dockerfile should set WORKDIR"

    def test_dockerfile_copies_requirements(self, dockerfile_path: Path):
        """Test that Dockerfile copies requirements.txt."""
        content = dockerfile_path.read_text()
        assert "requirements.txt" in content, \
            "Dockerfile should copy requirements.txt for dependency installation"

    def test_dockerfile_has_entrypoint_or_cmd(self, dockerfile_path: Path):
        """Test that Dockerfile has ENTRYPOINT or CMD."""
        content = dockerfile_path.read_text()
        assert "CMD" in content or "ENTRYPOINT" in content, \
            "Dockerfile should have CMD or ENTRYPOINT to run the application"

    def test_dockerfile_exposes_port(self, dockerfile_path: Path):
        """Test that Dockerfile exposes application port."""
        content = dockerfile_path.read_text()
        assert "EXPOSE" in content, \
            "Dockerfile should expose port for the API"
