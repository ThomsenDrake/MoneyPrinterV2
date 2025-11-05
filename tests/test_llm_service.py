"""
Unit tests for LLM Service (src/llm_service.py).
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestLLMService:
    """Tests for LLMService class."""

    def teardown_method(self):
        """Reset instances after each test."""
        from llm_service import LLMService
        LLMService.reset_instances()

    def test_initialization(self):
        """Test LLM service initialization."""
        from llm_service import LLMService

        service = LLMService(api_key="test-key", default_model="mistral-large-latest")

        assert service.api_key == "test-key"
        assert service.default_model == "mistral-large-latest"
        assert service._client is None

    def test_get_instance_creates_new(self):
        """Test that get_instance creates new instance."""
        from llm_service import LLMService

        service1 = LLMService.get_instance(api_key="key1")
        service2 = LLMService.get_instance(api_key="key2")

        assert service1 is not service2
        assert service1.api_key == "key1"
        assert service2.api_key == "key2"

    def test_get_instance_returns_cached(self):
        """Test that get_instance returns cached instance for same key."""
        from llm_service import LLMService

        service1 = LLMService.get_instance(api_key="test-key")
        service2 = LLMService.get_instance(api_key="test-key")

        assert service1 is service2

    def test_get_instance_with_model(self):
        """Test get_instance with custom model."""
        from llm_service import LLMService

        service = LLMService.get_instance(
            api_key="test-key",
            default_model="mistral-small-latest"
        )

        assert service.default_model == "mistral-small-latest"

    @patch('llm_service.Mistral')
    def test_client_property_lazy_initialization(self, mock_mistral_class):
        """Test that client is lazily initialized."""
        from llm_service import LLMService

        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")

        # Client should not be initialized yet
        assert service._client is None

        # Access client property
        client = service.client

        # Now client should be initialized
        assert client is mock_client
        mock_mistral_class.assert_called_once_with(api_key="test-key")

    @patch('llm_service.Mistral')
    def test_client_property_cached(self, mock_mistral_class):
        """Test that client is cached after first access."""
        from llm_service import LLMService

        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")

        # Access client multiple times
        client1 = service.client
        client2 = service.client
        client3 = service.client

        # Mistral should only be instantiated once
        assert mock_mistral_class.call_count == 1
        assert client1 is client2 is client3


class TestChatCompletion:
    """Tests for chat_completion method."""

    def teardown_method(self):
        """Reset instances after each test."""
        from llm_service import LLMService
        LLMService.reset_instances()

    @patch('llm_service.Mistral')
    def test_chat_completion_success(self, mock_mistral_class):
        """Test successful chat completion."""
        from llm_service import LLMService

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is the AI response"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        # Create service and make request
        service = LLMService(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]

        result = service.chat_completion(messages)

        # Verify result
        assert result == "This is the AI response"

        # Verify API was called correctly
        mock_client.chat.complete.assert_called_once_with(
            model="mistral-medium-latest",
            messages=messages,
            temperature=0.7
        )

    @patch('llm_service.Mistral')
    def test_chat_completion_with_custom_model(self, mock_mistral_class):
        """Test chat completion with custom model."""
        from llm_service import LLMService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        result = service.chat_completion(messages, model="mistral-large-latest")

        mock_client.chat.complete.assert_called_once_with(
            model="mistral-large-latest",
            messages=messages,
            temperature=0.7
        )

    @patch('llm_service.Mistral')
    def test_chat_completion_with_temperature(self, mock_mistral_class):
        """Test chat completion with custom temperature."""
        from llm_service import LLMService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        result = service.chat_completion(messages, temperature=0.3)

        mock_client.chat.complete.assert_called_once_with(
            model="mistral-medium-latest",
            messages=messages,
            temperature=0.3
        )

    @patch('llm_service.Mistral')
    def test_chat_completion_with_max_tokens(self, mock_mistral_class):
        """Test chat completion with max tokens."""
        from llm_service import LLMService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        result = service.chat_completion(messages, max_tokens=100)

        mock_client.chat.complete.assert_called_once_with(
            model="mistral-medium-latest",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )

    @patch('llm_service.Mistral')
    def test_chat_completion_exception(self, mock_mistral_class):
        """Test chat completion handles exceptions."""
        from llm_service import LLMService

        mock_client = MagicMock()
        mock_client.chat.complete.side_effect = Exception("API Error")
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception, match="API Error"):
            service.chat_completion(messages)


class TestGenerateScript:
    """Tests for generate_script convenience method."""

    def teardown_method(self):
        """Reset instances after each test."""
        from llm_service import LLMService
        LLMService.reset_instances()

    @patch('llm_service.Mistral')
    def test_generate_script(self, mock_mistral_class):
        """Test generate_script convenience method."""
        from llm_service import LLMService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated script content"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")

        result = service.generate_script(
            system_prompt="You are a script writer",
            user_prompt="Write a script about AI"
        )

        assert result == "Generated script content"

        # Verify messages were formatted correctly
        call_args = mock_client.chat.complete.call_args
        messages = call_args[1]["messages"]

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a script writer"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Write a script about AI"

    @patch('llm_service.Mistral')
    def test_generate_script_with_custom_model(self, mock_mistral_class):
        """Test generate_script with custom model."""
        from llm_service import LLMService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Script"

        mock_client = MagicMock()
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client

        service = LLMService(api_key="test-key")

        result = service.generate_script(
            system_prompt="System",
            user_prompt="User",
            model="mistral-large-latest"
        )

        call_args = mock_client.chat.complete.call_args
        assert call_args[1]["model"] == "mistral-large-latest"


class TestResetInstances:
    """Tests for reset_instances class method."""

    def test_reset_instances(self):
        """Test that reset_instances clears all cached instances."""
        from llm_service import LLMService

        # Create some instances
        service1 = LLMService.get_instance(api_key="key1")
        service2 = LLMService.get_instance(api_key="key2")

        assert len(LLMService._instances) == 2

        # Reset
        LLMService.reset_instances()

        assert len(LLMService._instances) == 0

        # New instances should be different
        service3 = LLMService.get_instance(api_key="key1")
        assert service3 is not service1


class TestConvenienceFunction:
    """Tests for create_llm_service convenience function."""

    def teardown_method(self):
        """Reset instances after each test."""
        from llm_service import LLMService
        LLMService.reset_instances()

    def test_create_llm_service(self):
        """Test create_llm_service convenience function."""
        from llm_service import create_llm_service

        service = create_llm_service(api_key="test-key")

        assert service.api_key == "test-key"
        assert service.default_model == "mistral-medium-latest"

    def test_create_llm_service_with_model(self):
        """Test create_llm_service with custom model."""
        from llm_service import create_llm_service

        service = create_llm_service(
            api_key="test-key",
            model="mistral-small-latest"
        )

        assert service.default_model == "mistral-small-latest"

    def test_create_llm_service_returns_cached(self):
        """Test that create_llm_service returns cached instance."""
        from llm_service import create_llm_service

        service1 = create_llm_service(api_key="test-key")
        service2 = create_llm_service(api_key="test-key")

        assert service1 is service2
