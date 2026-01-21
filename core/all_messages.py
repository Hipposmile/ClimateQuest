from django.utils.safestring import mark_safe

all_messages = {
    # --------
    #Allgemein
    # --------

    "not_authorized_to_visit": "Du hast nicht die Berechtigung, diese Seite zu besuchen.",
    "missing_required_inputs": "Es fehlen Pflichfelder",
    "invalid_admin_password": "Ungültiges Admin-Passwort",
    "invalid_action": "Ungültige Aktion",
    "notification_deleted": "Benachrichtigung erfolgreich gelöscht",
    "delete_notification_error": "interner Fehler: Benachrichtigung bereits gelöscht",
    "internal_error": "interner Fehler. Probiere es später erneut",
    "no_admin_auth": "Du darfst nicht auf die Admin-Funktionen zugreifen",
    "user_not_exist": "User existiert nicht",
    "not_is_truth": "Du musst bestätigen, dass alle Angaben der Wahrheit entsprechen",
    "too_long_input": "Ein oder mehrere Input-Felder sind zu lang",
    "not_a_number": "Der Input muss eine Zahl sein.",

    #Zeitraum
    "invalid_date_range": "Startdatum muss vor Enddatum liegen",
    "date_in_future": "Datum darf nicht in der Zukunft liegen",
    "date_in_past": "Datum darf nicht in der Vergangenheit liegen",
    "invalid_date": "Ungültiges Datum",
    "invalid_time_period": "Ungültiger Zeitraum",

    #--------
    #Community
    #--------

    #Create
    "community_exists": "Community mit diesem Namen existiert bereits",
    "community__invalid_family_credentials": "Family-Anmeldedaten ungültig",
    "community_created": "Community erfolgreich erstellt",
    "family_already_in_community": "Family ist bereits Teil der Community",

    #Join
    "community_joined": "Deine Family {family} ist der Community {community} beigetreten",
    "invalid_community_credentials": "Community-Anmeldedaten ungültig",

    #Login
    "community_id_missing": "Community ID wurde nicht übergeben",
    "community_not_found": "Community wurde nicht gefunden",
    "community__family_id_missing": "Family ID wurde nicht übergeben.",
    "community__family_not_found": "Family wurde nicht gefunden",
    "community__not_member_of_family": "Du bist nicht Mitglied der eingeloggten Family.",

    #Edit
    "community_name_changed": "Communityname erfolgreich geändert.",
    "community_password_changed": "Passwort erfolgreich geändert.",
    "community_admin_password_changed": "Admin-Passwort erfolgreich geändert.",
    "community__family_removed": "Family erfolgreich entfernt.",
    "family_left_community": "Deine Family hat die Community erfolgreich verlassen.",
    "community_deleted": "Community erfolgreich gelöscht",
    "community_chat_enabled": "Chat für die Community aktiviert",
    "community_chat_disabled": "Chat für die Community deaktiviert",

    "chat_disabled_for_community": "Der Chat für diese Community ist deaktiviert",
    # --------
    #Family
    # --------

    #Create
    "family_exists": "Family mit diesem Namen existiert bereits",
    "family_name_forbidden": "Du darfst \"worldwide ranking\" nicht als Family verwenden",
    "family_created": "Family erfolgreich erstellt",

    #Join
    "invalid_family_credentials": "Ungültige Family-Anmeldedaten.",
    "family_joined": "Du bist der Family {family.name} beigetreten.",
    "family_already_joined": "Du bist der Family {family.name} bereits beigetreten.",

    #Login
    "family_id_missing": "Family ID wurde nicht übergeben",
    "family_not_found": "Family wurde nicht gefunden",
    "not_part_of_family": "Du bist nicht Teil der Family {family.name}.",

    #Edit
    "family_name_changed": "Familyname erfolgreich geändert",
    "family_password_changed": "Passwort erfolgreich geändert",
    "family_admin_password_changed": "Admin-Passwort erfolgreich geändert",
    "family_user_removed": "User erfolgreich entfernt",
    "family_left": "Family erfolgreich verlassen",
    "family_chat_enabled": "Chat für die Family aktiviert",
    "family_chat_disabled": "Chat für die Family deaktiviert",
    "family_deleted": "Family erfolgreich gelöscht",
    "family_user_not_found": "Dieser User existiert in dieser Family nicht",

    #Allgemein
    "chat_disabled_for_family": "Der Chat für diese Family ist deaktiviert",
    "chat_not_enabled_for_worldwide_ranking": "Die Chatfunktion bei \"worldwide ranking\" ist nicht freigeschaltet",

    # --------
    #Personals
    # --------

    #Login
    "successfully_signed_up": "Erfolgreich registriert",
    "successfully_signed_up_email_not_verified": "Erfolgreich registriert, aber E-Mail-Adresse noch nicht verifiziert.",
    "robot": "Es besteht die Gefahr, dass du ein Roboter bist. Bitte versuche es erneut.",
    "invalid_login_data": "Ungültige Anmeldedaten.",
    "username_not_available": "Benutzername bereits vergeben",
    "invalid_email": "E-Mail-Adresse ungültig",
    "email_not_available": "E-Mail-Adresse bereits vergeben",
    "nutzungsbedingungen_not_accepted": "Du musst die Nutzungsbedingungen akzeptieren",
    "datenschutz_not_accepted": "Du musst die Datenschutzerklärung akzeptieren",
    "invalid_verification_link": "Ungültiger Verifizierungslink",

    #Edit
    "invalid_password": "Passwort ist falsch",
    "username_belongs_to_you": "Benutzername gehört bereits dir",
    "username_changed": "Benutzername erfolgreich geändert",
    "password_changed": "Passwort erfolgreich geändert",
    "email_changed": "E-Mail-Adresse erfolgreich geändert",
    "mailinglist_enabled": "E-Mail Benachrichtigungen aktiviert",
    "mailinglist_disabled": "E-Mail Benachrichtigungen deaktiviert",
    "account_deleted": "Account erfolgreich gelöscht",
    "email_not_found": "E-Mail-Adresse nicht vorhanden",
    "password_reset_mail_sent": "Wir haben dir eine Nachricht mit deinem Benutzernamen und einem neuen, zufällig generiertem Passwort geschickt. Melde dich damit an und ändere aus Sicherheitsgründen möglichst bald dein Passwort unter \"Profil bearbeiten\".",
    "password_reset_error": "Ein Fehler ist beim Zurücksetzen des Passwortes aufgetreten",
    "successfully_changed_email": "E-Mail-Adresse erfolgreich geändert. Ein Aktivierungslink wurde an diese Adresse gesendet.",
    "successfully_changed_email_no_email": "E-Mail-Adresse erfolgreich geändert. Du hast jetzt keine E-Mail Adresse mehr hinterlegt und musst daher nichts verifizieren.",
    "no_email_to_verify": "Du hast keine E-Mail-Adresse angegeben und musst daher nichts verifizieren",
    "successfully_changed_statement": "Du hast erfolgreich dein Statement geupdated.",
    "user_is_active_at_verify": "Du bist bereits verifiziert. Logge dich direkt ein.",
    "email_verified": "E-Mail-Adresse erfolgreich verifiziert",
    "verification_email_resent": "Verifizierungs-E-Mail erfolgreich erneut gesendet",
    "successfully_changed_goal": "Wöchentliches Ziel erfolgreich geändert.",
    "weekly_goal_too_small": "Das wöchentliche Ziel ist zu klein.",


    # --------
    #Aktion
    # --------

    "select_action_type": "Wähle einen Aktionstyp aus",
    "enter_quantity": "Gib eine Menge an",
    "invalid_quantity": "Ungültige Menge",
    "quantity_positive": "Die Menge muss positiv sein",
    "invalid_action_type": "Ungültiger Aktionstyp",
    "action_added": "Aktion erfolgreich hinzugefügt",
    "action_name_missing": "Name der Aktion wurde nicht übergeben.",
    "action_id_missing": "ID der Aktion wurde nicht übergeben.",
    "action_not_found": "Aktion existiert nicht.",
    "action_edited": "Aktion erfolgreich bearbeitet",
    "action_deleted": "Aktion erfolgreich gelöscht",
    "action_invalid_quantity": "Ungültige Menge",
    "max_action_quantity": mark_safe("Die angegebene Menge ist zu hoch, um realistisch zu sein. Weitere Informationen findest du in <a href='https://climate-quest.de/artikel/artikel_detail/9'>diesem Artikel</a>."),
    "action_too_past": "Das Datum liegt zu weit in der Vergangenheit, um realistisch zu sein.",

    # --------
    #Event
    # --------

    "date_must_be_tomorrow": "Das Datum muss mindestens einen Tag in der Zukunft liegen.",
    "successfully_created_event": "Event erfolgreich erstellt",
    "successfully_edited_event": "Event erfolgreich bearbeitet",
    "successfully_deleted_event": "Event erfolgreich gelöscht",
    "event_not_existing": "Event existiert nicht",
    "left_event": "Erfolgreich aus Event ausgetreten",
    "joined_event": "Dem Event erfolgreich beigetreten",
    "event__user_is_creator": "Du bist der Creator dieses Events und kannst daher nicht noch Teilnehmer werden.",
    "event__no_right_to_edit": "Du hast keine Berechtigungen, dieses Event zu bearbeiten",
    "successfully_asked_question": "Frage erfolgreich gestellt.",
    "successfully_answered_question": "Frage erfolgreich beantwortet.",
    "teilnehmeranzahl_search_keyword_not_a_number": "Wenn du nach der Teilnehmeranzahl filterst, muss das Suchwort eine Zahl sein",

    # --------
    #Artikel
    # --------

    "successfully_created_artikel": "Artikel erfolgreich erstellt",
    "successfully_edited_artikel": "Artikel erfolgreich bearbeitet",
    "successfully_deleted_artikel": "Artikel erfolgreich gelöscht",
    "artikel_not_existing": "Artikel existiert nicht",
    "artikel__no_right_to_edit": "Du hast keine Berechtigungen, diesen Artikel zu bearbeiten",
    "successfully_asked_comment": "Kommentar erfolgreich gestellt.",
    "successfully_answered_comment": "Kommentar erfolgreich beantwortet.",
    "successfully_added_like": "Du hast den Artikel erfolgreich geliket.",
    "successfully_removed_like": "Du hast den Like zum Artikel erfolgreich entfernt.",
    "likes_search_keyword_not_a_number": "Wenn du nach Likes filterst, muss das Suchwort eine Zahl sein",

    # --------
    #Forum
    # --------

    "post_not_found": "Post nicht gefunden",

    # --------
    #Users
    # --------
    "user_not_found": "User nicht gefunden",
    "msg_created": "Nachricht erfolgreich gesendet",
    "reported_user": "Der User wurde erfolgreich gemeldet.",

    # --------
    #Admin
    # --------
    "admin__user_not_found": "User wurde nicht gefunden",
    "admin__family_not_found": "Family wurde nicht gefunden",
    "admin__community_not_found": "Community wurde nicht gefunden",
    "admin__event_not_found": "Event wurde nicht gefunden",
    "admin__invalid_receiver_type": "Ungültiger Empfänger-Typ der Nachricht",
    "admin__successfully_sent_notification": "Benachrichtigung erfolgreich an alle Empfänger gesendet",
    "user_deleted": "User erfolgreich gelöscht",
    "worldwide_ranking_valid_passwords": "Die Passwörter der Family worldwide_ranking sind aktuell.",
    "worldwide_ranking_invalid_password": "Die Passwörter der Family worldwide-Ranking waren ungültig und entsprechend der gespeicherten Passwörter geändert.",
    "added_everyone_user_erweitert": "Jedem User wurde ein UserErweitert hinzugefügt, sofern noch nicht vorhanden",

    # --------
    #Presents
    # --------
    "present_created": "Geschenkseite erfolgreich erstellt",
    "present_not_found": "Geschenkseite nicht gefunden",
    "congratulation_added": "Glückwunschnachricht erfolgreich hinzugefügt",
    "present_deleted": "Geschenkseite erfolgreich gelöscht",
}