from dataclasses import dataclass


@dataclass
class AgentCredentials:
    openai_model = None
    openai_key = None
    azure_endpoint = None
    azure_deployment = None
    api_version = None
    api_key = None
    github_token = None
    github_model = None
    github_default_token = True

    def has_valid_azure_credentials(self):
        return (self.azure_endpoint is not None) and (self.azure_deployment is not None) \
            and (self.api_key is not None) and (self.api_version is not None)

    def has_valid_openai_credentials(self):
        return (self.openai_model is not None) and (self.openai_key is not None)

    def has_valid_github_credentials(self):
        return ((self.github_token is not None) and (self.openai_model is not None)) or\
            (self.github_default_token and (self.openai_model is not None))

    def has_any_valid_credentials(self):
        return self.has_valid_openai_credentials() or self.has_valid_azure_credentials()\
            or self.has_valid_github_credentials()
