"""
Health checks for API keys and external services.

This module validates API keys and service connectivity on startup,
helping users identify configuration issues early.
"""

import logging
from typing import List, Optional, Tuple

from config import (
    get_assembly_ai_api_key,
    get_mistral_api_key,
    get_venice_api_key,
)
from constants import DEFAULT_HTTP_TIMEOUT
from http_client import get_http_client
from status import error, info, success, warning


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        service_name: str,
        passed: bool,
        message: str,
        details: Optional[str] = None,
    ):
        """
        Initialize health check result.

        Args:
            service_name: Name of the service checked
            passed: Whether the check passed
            message: Result message
            details: Optional detailed information
        """
        self.service_name = service_name
        self.passed = passed
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """String representation of the result."""
        status = "✓ PASS" if self.passed else "✗ FAIL"
        result = f"{status} - {self.service_name}: {self.message}"
        if self.details:
            result += f"\n  Details: {self.details}"
        return result


class HealthChecker:
    """
    Service for checking API key validity and service connectivity.

    Validates that all required API keys are configured and can
    successfully authenticate with their respective services.
    """

    @staticmethod
    def check_mistral_ai() -> HealthCheckResult:
        """
        Check Mistral AI API connectivity.

        Returns:
            HealthCheckResult: Result of the health check
        """
        try:
            api_key = get_mistral_api_key()

            if not api_key or api_key.strip() == "":
                return HealthCheckResult(
                    "Mistral AI",
                    False,
                    "API key not configured",
                    "Set mistral_api_key in config.json",
                )

            # Try to create a Mistral client (lightweight check)
            from mistralai import Mistral

            # Simple validation - just check if client can be created
            # (Full validation would require an API call which costs money)
            Mistral(api_key=api_key)

            return HealthCheckResult(
                "Mistral AI",
                True,
                "API key configured",
                "Note: Full validation requires an API call",
            )

        except ImportError:
            return HealthCheckResult(
                "Mistral AI",
                False,
                "mistralai package not installed",
                "Run: pip install mistralai",
            )
        except Exception as e:
            return HealthCheckResult("Mistral AI", False, "Configuration error", str(e))

    @staticmethod
    def check_venice_ai() -> HealthCheckResult:
        """
        Check Venice AI API key configuration.

        Returns:
            HealthCheckResult: Result of the health check
        """
        try:
            api_key = get_venice_api_key()

            if not api_key or api_key.strip() == "":
                return HealthCheckResult(
                    "Venice AI",
                    False,
                    "API key not configured",
                    "Set venice_api_key in config.json (optional - only needed for image generation)",
                )

            # Venice AI doesn't have a simple validation endpoint
            # Just check if key is configured
            return HealthCheckResult(
                "Venice AI",
                True,
                "API key configured",
                "Used for image generation with qwen-image model",
            )

        except Exception as e:
            return HealthCheckResult("Venice AI", False, "Configuration error", str(e))

    @staticmethod
    def check_assembly_ai() -> HealthCheckResult:
        """
        Check AssemblyAI API connectivity.

        Returns:
            HealthCheckResult: Result of the health check
        """
        try:
            api_key = get_assembly_ai_api_key()

            if not api_key or api_key.strip() == "":
                return HealthCheckResult(
                    "AssemblyAI",
                    False,
                    "API key not configured",
                    "Set assembly_ai_api_key in config.json (optional - only needed for transcription)",
                )

            # AssemblyAI client validation
            import assemblyai as aai

            aai.settings.api_key = api_key

            # Simple check - just verify key is set
            return HealthCheckResult(
                "AssemblyAI",
                True,
                "API key configured",
                "Used for video transcription",
            )

        except ImportError:
            return HealthCheckResult(
                "AssemblyAI",
                False,
                "assemblyai package not installed",
                "Run: pip install assemblyai",
            )
        except Exception as e:
            return HealthCheckResult("AssemblyAI", False, "Configuration error", str(e))

    @staticmethod
    def check_http_connectivity() -> HealthCheckResult:
        """
        Check HTTP client connectivity.

        Returns:
            HealthCheckResult: Result of the health check
        """
        try:
            http_client = get_http_client()

            # Test with a reliable endpoint
            response = http_client.get("https://www.google.com", timeout=DEFAULT_HTTP_TIMEOUT)

            if response.status_code == 200:
                return HealthCheckResult(
                    "HTTP Client",
                    True,
                    "Internet connectivity verified",
                    "Connection pooling active",
                )
            else:
                return HealthCheckResult(
                    "HTTP Client",
                    False,
                    f"Unexpected status code: {response.status_code}",
                )

        except Exception as e:
            return HealthCheckResult(
                "HTTP Client",
                False,
                "Internet connectivity issues",
                f"Error: {str(e)}",
            )

    @classmethod
    def run_all_checks(cls, verbose: bool = True) -> Tuple[List[HealthCheckResult], bool]:
        """
        Run all health checks.

        Args:
            verbose: Whether to print results to console

        Returns:
            Tuple[List[HealthCheckResult], bool]: List of results and overall pass status
        """
        checks = [
            ("HTTP Connectivity", cls.check_http_connectivity),
            ("Mistral AI", cls.check_mistral_ai),
            ("Venice AI", cls.check_venice_ai),
            ("AssemblyAI", cls.check_assembly_ai),
        ]

        results = []
        all_critical_passed = True

        if verbose:
            info("\n========== API HEALTH CHECKS ==========")

        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append(result)

                if verbose:
                    if result.passed:
                        success(f"  {result}")
                    else:
                        # HTTP and Mistral are critical, others are warnings
                        if check_name in ["HTTP Connectivity", "Mistral AI"]:
                            error(f"  {result}")
                            all_critical_passed = False
                        else:
                            warning(f"  {result}")

            except Exception as e:
                result = HealthCheckResult(check_name, False, "Check failed", str(e))
                results.append(result)
                if verbose:
                    error(f"  {result}")
                all_critical_passed = False

        if verbose:
            info("========================================\n")

            if all_critical_passed:
                success("All critical health checks passed!")
            else:
                error("Some critical health checks failed. Please review the errors above.")

        return results, all_critical_passed

    @classmethod
    def validate_startup(cls) -> bool:
        """
        Run startup validation checks.

        Returns:
            bool: True if all critical checks passed

        Example:
            >>> if not HealthChecker.validate_startup():
            ...     sys.exit(1)
        """
        logging.info("Running startup health checks...")
        _, all_passed = cls.run_all_checks(verbose=True)

        if not all_passed:
            logging.error("Startup health checks failed")
            warning("\nWARNING: Some health checks failed. The application may not work correctly.")
            warning("Please check your configuration in config.json")
            return False

        logging.info("All startup health checks passed")
        return True


# Convenience function
def run_health_checks(verbose: bool = True) -> bool:
    """
    Run all health checks.

    Args:
        verbose: Whether to print results to console

    Returns:
        bool: True if all critical checks passed
    """
    _, all_passed = HealthChecker.run_all_checks(verbose=verbose)
    return all_passed
