import requests
from bs4 import BeautifulSoup
from .encryption_utils.encryption_utils import (
    decrypt_object,
    encrypt_object,
)
from .url_constants import Urls
from typing import Dict, Any
import hashlib

# LOGGING________________________________________________________________________________
from .logging_config import configure_logging

logger = configure_logging(__name__)


class SessionManager:
    def __init__(self, url: str, user: str, password: str):
        """
        Der Konstruktor (__init__) initialisiert die SessionManager-Instanz mit den erforderlichen Informationen wie der Basis-URL,
        den Anmeldeinformationen und URLs zur Validierung. Es erstellt auch einen geheimen Schlüssel aus Benutzername und Passwort
        und legt den Dateinamen für die verschlüsselte Sitzungsdatei fest.
        """
        # session
        self.base_url = url
        self.valdidate_url = Urls.STARTSEITE.value
        self._user = user
        self._password = password
        self._session = None

        # secret
        binary_string = (user + password).encode("utf-8")
        self._key = binary_string.ljust(32, b"\x00")
        self._session_file = self._generate_filename(user, password)

    def _generate_filename(self, user: str, password: str) -> str:
        """
        Generate a unique and consistent filename based on the given user and password.

        Args:
            user (str): The username.
            password (str): The password.

        Returns:
            str: The generated filename.
        """
        combined_string = user + password
        hashed_string = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()
        return f"{hashed_string}.session"

    def _load_session(self) -> bool:
        """Diese Methode lädt eine vorhandene requests.Session aus einer verschlüsselten Datei oder erstellt eine neue Sitzung, wenn keine vorhanden ist. Sie gibt zurück, ob die geladene Sitzung gültig ist oder nicht.

        Returns:
            A requests.Session object.
        """

        try:
            self._session = decrypt_object(self._key, self._session_file)
            logger.info("Session geladen")
        except Exception:
            self._session = requests.Session()
            logger.info("Neue Session erstellt")

        return self._validate_session()

    def _validate_session(self) -> bool:
        """Diese Methode überprüft, ob die angegebene Sitzung gültig ist, indem sie prüft, ob der Benutzer eingeloggt ist. Wenn der Benutzer nicht eingeloggt ist, wird die Methode logon aufgerufen, um sich anzumelden.

        Args:
            session: A requests.Session object.

        Returns:
            A validated requests.Session object.
        """
        response = self._session.get(f"{self.base_url}{self.valdidate_url}")
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").text.strip().upper().lstrip("\ufeff")
        compare_val = "Smart-Heat-OS - Temperaturüberwachung".strip().upper()

        logger.debug(f"_validate_session :{title == compare_val}")
        return title == compare_val

    def logon(self, login_url: str) -> requests.Session:
        """Diese Methode meldet den Benutzer an, indem sie die Anmeldedaten aus einer verschlüsselten Datei lädt und einen POST-Request mit diesen Anmeldedaten sendet. Wenn die Anmeldung erfolgreich ist, wird die Sitzung gespeichert und zurückgegeben.

        Args:
            session: A requests.Session object.

        Returns:
            A valid requests.Session object if login was successful, else None.
        """
        if self._load_session():
            logger.info("Session konnte wiederhergestellt werden.")
            return self._session

        self._session.get(f"{self.base_url}{login_url}")
        cookie_dict = self._session.cookies.get_dict()
        payload = {
            "mail": self._user,
            "pw": self._password,
            "csrfmiddlewaretoken": cookie_dict["csrftoken"],
        }
        response = self._session.post(f"{self.base_url}{login_url}", data=payload)

        if response.status_code == 200:
            logger.info("Anmeldung erfolgreich")
            encrypt_object(self._session, self._key, self._session_file)
            return self._session
        else:
            logger.error("Anmeldung fehlgeschlagen")
            logger.error(response.text)
            return None
