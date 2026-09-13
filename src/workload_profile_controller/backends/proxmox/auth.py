from dataclasses import dataclass


@dataclass(frozen=True)
class ProxmoxToken:
    user: str
    token_name: str
    secret: str

    def authorization_header(self) -> str:
        return (
            "PVEAPIToken="
            f"{self.user}!{self.token_name}="
            f"{self.secret}"
        )
