from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

all_messages = {
    # --------
    # Allgemein
    # --------

    "not_authorized_to_visit": _("Du hast nicht die Berechtigung, diese Seite zu besuchen"),
    "missing_required_inputs": _("Es fehlen Pflichfelder"),
    "invalid_admin_password": _("Ungültiges Admin-Passwort"),
    "invalid_action": _("Ungültige Aktion"),
    "notification_deleted": _("Benachrichtigung erfolgreich gelöscht"),
    "delete_notification_error": _("Interner Fehler: Benachrichtigung bereits gelöscht"),
    "internal_error": _("Interner Fehler Probiere es später erneut"),
    "no_admin_auth": _("Du darfst nicht auf die Admin-Funktionen zugreifen"),
    "user_not_exist": _("User existiert nicht"),
    "not_is_truth": _("Du musst bestätigen, dass alle Angaben der Wahrheit entsprechen"),
    "too_long_input": _("Ein oder mehrere Input-Felder sind zu lang"),
    "not_a_number": _("Der Input muss eine Zahl sein"),

    # Zeitraum
    "invalid_date_range": _("Startdatum muss vor Enddatum liegen"),
    "date_in_future": _("Datum darf nicht in der Zukunft liegen"),
    "date_in_past": _("Datum darf nicht in der Vergangenheit liegen"),
    "invalid_date": _("Ungültiges Datum"),
    "invalid_time_period": _("Ungültiger Zeitraum"),

    # --------
    # Community
    # --------

    # Create
    "community_exists": _("Community mit diesem Namen existiert bereits"),
    "community__invalid_family_credentials": _("Family-Anmeldedaten ungültig"),
    "community_created": _("Community erfolgreich erstellt"),
    "family_already_in_community": _("Family ist bereits Teil der Community"),

    # Join
    "community_joined": _("Deine Family {family} ist der Community {community} beigetreten"),
    "invalid_community_credentials": _("Community-Anmeldedaten ungültig"),

    # Login
    "community_id_missing": _("Community ID wurde nicht übergeben"),
    "community_not_found": _("Community wurde nicht gefunden"),
    "community__family_id_missing": _("Family ID wurde nicht übergeben"),
    "community__family_not_found": _("Family wurde nicht gefunden"),
    "community__not_member_of_family": _("Du bist nicht Mitglied der eingeloggten Family"),

    # Edit
    "community_name_changed": _("Communityname erfolgreich geändert"),
    "community_password_changed": _("Passwort erfolgreich geändert"),
    "community_admin_password_changed": _("Admin-Passwort erfolgreich geändert"),
    "community__family_removed": _("Family erfolgreich entfernt"),
    "family_left_community": _("Deine Family hat die Community erfolgreich verlassen"),
    "community_deleted": _("Community erfolgreich gelöscht"),
    "community_chat_enabled": _("Chat für die Community aktiviert"),
    "community_chat_disabled": _("Chat für die Community deaktiviert"),

    "chat_disabled_for_community": _("Der Chat für diese Community ist deaktiviert"),
    # --------
    # Family
    # --------

    # Create
    "family_exists": _("Family mit diesem Namen existiert bereits"),
    "family_name_forbidden": _("Du darfst \"worldwide ranking\" nicht als Family verwenden"),
    "family_created": _("Family erfolgreich erstellt"),

    # Join
    "invalid_family_credentials": _("Ungültige Family-Anmeldedaten"),
    "family_joined": _("Du bist der Family {familyname} beigetreten"),
    "family_already_joined": _("Du bist der Family {familyname} bereits beigetreten"),

    # Login
    "family_id_missing": _("Family ID wurde nicht übergeben"),
    "family_not_found": _("Family wurde nicht gefunden"),
    "not_part_of_family": _("Du bist nicht Teil der Family {familyname}"),

    # Edit
    "family_name_changed": _("Familyname erfolgreich geändert"),
    "family_password_changed": _("Passwort erfolgreich geändert"),
    "family_admin_password_changed": _("Admin-Passwort erfolgreich geändert"),
    "family_user_removed": _("User erfolgreich entfernt"),
    "family_left": _("Family erfolgreich verlassen"),
    "family_chat_enabled": _("Chat für die Family aktiviert"),
    "family_chat_disabled": _("Chat für die Family deaktiviert"),
    "family_deleted": _("Family erfolgreich gelöscht"),
    "family_user_not_found": _("Dieser User existiert in dieser Family nicht"),

    # Allgemein
    "chat_disabled_for_family": _("Der Chat für diese Family ist deaktiviert"),
    "chat_not_enabled_for_worldwide_ranking": _("Die Chatfunktion bei \"worldwide ranking\" ist nicht freigeschaltet"),

    # --------
    # Personals
    # --------

    # Login
    "successfully_signed_up": _("Erfolgreich registriert"),
    "successfully_signed_up_email_not_verified": _("Erfolgreich registriert, aber E-Mail-Adresse noch nicht verifiziert"),
    "robot": _("Es besteht die Gefahr, dass du ein Roboter bist Bitte versuche es erneut"),
    "invalid_login_data": _("Ungültige Anmeldedaten"),
    "username_not_available": _("Username bereits vergeben"),
    "invalid_email": _("E-Mail-Adresse ungültig"),
    "email_not_available": _("E-Mail-Adresse bereits vergeben"),
    "nutzungsbedingungen_not_accepted": _("Du musst die Nutzungsbedingungen akzeptieren"),
    "datenschutz_not_accepted": _("Du musst die Datenschutzerklärung akzeptieren"),
    "invalid_verification_link": _("Ungültiger Verifizierungslink"),

    # Edit
    "invalid_password": _("Passwort ist falsch"),
    "username_belongs_to_you": _("Username gehört bereits dir"),
    "username_changed": _("Username erfolgreich geändert"),
    "password_changed": _("Passwort erfolgreich geändert"),
    "email_changed": _("E-Mail-Adresse erfolgreich geändert"),
    "mailinglist_enabled": _("E-Mail Benachrichtigungen aktiviert"),
    "mailinglist_disabled": _("E-Mail Benachrichtigungen deaktiviert"),
    "allows_data_view_enabled": _("Persönliche Daten Ansicht aktiviert"),
    "allows_data_view_disabled": _("Persönliche Daten Ansicht blockiert"),
    "account_deleted": _("Account erfolgreich gelöscht"),
    "email_not_found": _("E-Mail-Adresse nicht vorhanden"),
    "password_reset_mail_sent": _("Wir haben dir eine Nachricht mit deinem Usernamen und einem neuen, zufällig generiertem Passwort geschickt. Melde dich damit an und ändere aus Sicherheitsgründen möglichst bald dein Passwort unter \"Profil bearbeiten\""),
    "password_reset_error": _("Ein Fehler ist beim Zurücksetzen des Passwortes aufgetreten"),
    "successfully_changed_email": _("E-Mail-Adresse erfolgreich geändert. Ein Aktivierungslink wurde an diese Adresse gesendet"),
    "successfully_changed_email_no_email": _("E-Mail-Adresse erfolgreich geändert. Du hast jetzt keine E-Mail Adresse mehr hinterlegt und musst daher nichts verifizieren"),
    "no_email_to_verify": _("Du hast keine E-Mail-Adresse angegeben und musst daher nichts verifizieren"),
    "successfully_changed_statement": _("Du hast erfolgreich dein Statement geupdated"),
    "user_is_active_at_verify": _("Du bist bereits verifiziert. Logge dich direkt ein"),
    "email_verified": _("E-Mail-Adresse erfolgreich verifiziert"),
    "verification_email_resent": _("Verifizierungs-E-Mail erfolgreich erneut gesendet"),
    "successfully_changed_goal": _("Wöchentliches Ziel erfolgreich geändert"),
    "weekly_goal_too_small": _("Das wöchentliche Ziel ist zu klein"),
    "activated_tour_banner": _("Die Tour-Banner werden jetzt angezeigt"),
    "deactivated_tour_banner": _("Die Tour-Banner werden nicht mehr angezeigt"),

    "error_planting_tree": _("Beim Pflanzen deines Baumes ist ein Fehler aufgetreten"),

    # --------
    # Aktion
    # --------

    "select_action_type": _("Wähle einen Aktionstyp aus"),
    "enter_quantity": _("Gib eine Menge an"),
    "invalid_quantity": _("Ungültige Menge"),
    "quantity_positive": _("Die Menge muss positiv sein"),
    "invalid_action_type": _("Ungültiger Aktionstyp"),
    "action_added": _("Aktion erfolgreich hinzugefügt"),
    "action_name_missing": _("Name der Aktion wurde nicht übergeben"),
    "action_id_missing": _("ID der Aktion wurde nicht übergeben"),
    "action_not_found": _("Aktion existiert nicht"),
    "action_edited": _("Aktion erfolgreich bearbeitet"),
    "action_deleted": _("Aktion erfolgreich gelöscht"),
    "action_invalid_quantity": _("Ungültige Menge"),
    "max_action_quantity": mark_safe(
        _("Die angegebene Menge ist zu hoch, um realistisch zu sein. Weitere Informationen findest du in <a href='https://climate-questde/artikel/artikel_detail/9'>diesem Artikel</a>")),
    "action_too_past": mark_safe(_("Das angegebene Datum liegt zu weit in der Vergangenheit. Weitere Informationen findest du in <a href='https://climate-questde/artikel/artikel_detail/18'>diesem Artikel</a>")),
    "action_already_set_in_period": _("Diese oder eine verwandte Aktion wurde im gleichen Zeitraum schon einmal eingetragen"),

    "tracking_action": _("Aktion wird jetzt getrackt"),
    "forbidden_tracking_action": _("Aktion kann nicht getrackt werden, da eine verwandte Aktion bereits getrackt wird."),
    "stopped_tracking": _("Aktion wird nicht mehr getrackt"),

    # --------
    # Event
    # --------

    "date_must_be_tomorrow": _("Das Datum muss mindestens einen Tag in der Zukunft liegen"),
    "successfully_created_event": _("Event erfolgreich erstellt"),
    "successfully_edited_event": _("Event erfolgreich bearbeitet"),
    "successfully_deleted_event": _("Event erfolgreich gelöscht"),
    "event_not_existing": _("Event existiert nicht"),
    "left_event": _("Erfolgreich aus Event ausgetreten"),
    "joined_event": _("Dem Event erfolgreich beigetreten"),
    "event__user_is_creator": _("Du bist der Creator dieses Events und kannst daher nicht noch Teilnehmer werden"),
    "event__no_right_to_edit": _("Du hast keine Berechtigungen, dieses Event zu bearbeiten"),
    "successfully_asked_question": _("Frage erfolgreich gestellt"),
    "successfully_answered_question": _("Frage erfolgreich beantwortet"),
    "teilnehmeranzahl_search_keyword_not_a_number": _("Wenn du nach der Teilnehmeranzahl filterst, muss das Suchwort eine Zahl sein"),

    # --------
    # Artikel
    # --------

    "successfully_created_artikel": _("Artikel erfolgreich erstellt"),
    "successfully_edited_artikel": _("Artikel erfolgreich bearbeitet"),
    "successfully_deleted_artikel": _("Artikel erfolgreich gelöscht"),
    "artikel_not_existing": _("Artikel existiert nicht"),
    "artikel__no_right_to_edit": _("Du hast keine Berechtigungen, diesen Artikel zu bearbeiten"),
    "successfully_asked_comment": _("Kommentar erfolgreich gestellt"),
    "successfully_answered_comment": _("Kommentar erfolgreich beantwortet"),
    "successfully_added_like": _("Du hast den Artikel erfolgreich gelikt"),
    "successfully_removed_like": _("Du hast den Like zum Artikel erfolgreich entfernt"),
    "likes_search_keyword_not_a_number": _("Wenn du nach Likes filterst, muss das Suchwort eine Zahl sein"),
    "successfully_verified_article": _("Artikel erfolgreich verifiziert"),
    "successfully_unverified_article": _("Verifizierung erfolgreich gelöscht"),
    "successfully_blocked_article": _("Erfolgreich Artikel gesperrt"),
    "successfully_unblocked_article": _("Sperrung erfolgreich gelöscht"),
    "not_allowed_to_like_own_article": _("Du darfst deinen eigenen Artikel nicht liken"),

    # --------
    # Forum
    # --------

    "post_not_found": _("Post nicht gefunden"),

    # --------
    # Users
    # --------
    "user_not_found": _("User nicht gefunden"),
    "msg_created": _("Nachricht erfolgreich gesendet"),
    "reported_user": _("Der User wurde erfolgreich gemeldet"),
    "user_blocked_view": _("Der User hat die Ansicht seiner Daten geblockt"),

    # --------
    # Admin
    # --------
    "admin__user_not_found": _("User wurde nicht gefunden"),
    "admin__family_not_found": _("Family wurde nicht gefunden"),
    "admin__community_not_found": _("Community wurde nicht gefunden"),
    "admin__event_not_found": _("Event wurde nicht gefunden"),
    "admin__invalid_receiver_type": _("Ungültiger Empfänger-Typ der Nachricht"),
    "admin__successfully_sent_notification": _("Benachrichtigung erfolgreich an alle Empfänger gesendet"),
    "user_deleted": _("User erfolgreich gelöscht"),
    "worldwide_ranking_valid_passwords": _("Die Passwörter der Family worldwide_ranking sind aktuell"),
    "worldwide_ranking_invalid_password": _("Die Passwörter der Family worldwide-Ranking waren ungültig und entsprechend der gespeicherten Passwörter geändert"),
    "added_everyone_user_erweitert": _("Jedem User wurde ein UserErweitert hinzugefügt, sofern noch nicht vorhanden"),

    # --------
    # Petition
    # --------
    "petition_added": _("Petition hinzugefügt"),
    "petition_not_found": _("Petition nicht gefunden"),
    "petition_signed": _("Petition erfolgreich unterschrieben"),
    "petition_unsigned": _("Unterschrift erfolgreich entfernt"),
    "signs_search_keyword_not_a_number": _("Wenn du nach Unterschriften filterst, muss das Suchwort eine Zahl sein"),
    "goal_not_a_number": _("Das Ziel muss eine Zahl sein"),
    "goal_too_small": _("Das Ziel muss mindestens 10 sein"),
    "successfully_updated_goal": _("Ziel erfolgreich aktualisiert"),
    "added_success": _("Du hast die Petition zum Erfolg erklärt!"),
    "removed_success": _("Du hast den Erfolg der Petition gelöscht"),
    # --------
    # Image Upload
    # --------
    "size_exceeded_maximum": _("Maximal {max_size_mb} MB erlaubt"),
    "invalid_file_extension": _("Ungültige Dateiendung"),
    "invalid_img": _("Ungültiges Bild"),
    "invalid_file_type": _("Ungültiger Dateityp"),
    "invalid_mime_type": _("Ungültiger MIME-Typ"),
    "invalid_img_proportions": _("Ungültiges Seitenverhältnis")
}
