# Bugs fixed

Each entry: file – what was wrong – how it was fixed – test that proves it.
Every test listed here was written to fail against the old code first.

## Shared helpers (`utils/functions.py`)

| File | Problem | Fix | Test |
|---|---|---|---|
| `utils/functions.py` `generate_random_password` | Reset passwords were generated with `random` (not cryptographically secure, predictable). | Uses `secrets.choice`. | `test_generate_random_password_uses_cryptographic_source` |
| `utils/functions.py` `get_klimapunkte` | `Aktion.impact` loaded the related `AktionenListe` row for every action (N+1) and summed in Python. | Querysets are summed in one SQL aggregate. | `test_get_klimapunkte_runs_constant_queries` |
| `utils/functions.py` `get_level` | Crashed (`AttributeError`) when the user had fewer points than the lowest level or no levels existed. | Returns `current_level=None`, `level_number=0` and the first level as `next_level`. | `test_get_level_without_level_zero_does_not_crash`, `test_get_level_without_any_level` |
| `utils/functions.py` `get_family_rank_from_user` | `StopIteration` (HTTP 500) for users that are not members of the family; recomputed every member's points with several queries each. | Returns `None` for non-members; three aggregate queries for the whole family. | `test_family_rank_for_non_member_is_none`, `test_family_rank_optimized_query_count_is_constant` |
| `utils/functions.py` `send_mail_function` | Crashed for `request=None`; continued after reporting missing arguments; HTML of the mail contained the unescaped subject and a literal `{{ request.csp_style_nonce }}`; used `settingsprod` (imports production settings in every environment) for the sender address. | Single mail template with escaped subject, sender from `DEFAULT_FROM_EMAIL`, early return after reporting errors. | `test_send_mail_escapes_subject_in_html`, `test_send_mail_without_request_does_not_crash`, `test_send_mail_missing_arguments_is_reported` |
| `utils/functions.py` `create_internal_error` | Wrote to the relative path `logs/errors.log`; if the directory did not exist every error handler (400/403/CSRF pages) crashed with `FileNotFoundError`. | Uses `settings.LOGS_DIR`, created on demand; works without a request. | `test_create_internal_error_anonymous_without_message` |
| `utils/functions.py` `create_notification` | Push text was cut at `<span>` but the emoji markup is `<span class="emoji">`, so raw HTML ended up in push notifications. | Cuts at `<span\b`. | `test_create_notification_german_and_english` |
| `utils/functions.py` `send_ios_push` | No timeout (a hanging APNs connection blocked the request forever); raised bare `Exception`. | 10 s timeout, `RuntimeError`. | `test_send_ios_push` |
| `utils/functions.py` week calculations | `date.today()` (server time zone) instead of the project time zone `Europe/Berlin`. | `timezone.localdate()`. | `test_streak`, `test_weekly_goal` |

## Actions (`aktionen`, `users`)

| File | Problem | Fix | Test |
|---|---|---|---|
| `aktionen/views.py` add | `nan`/`inf` quantities passed validation; huge quantities of timely actions raised `OverflowError` (HTTP 500). | Non-finite numbers are rejected; overflow is treated as "date too far in the past". | `test_add_action_validation_errors[nan]`, `test_add_huge_timely_quantity_is_rejected_not_crashing` |
| `aktionen/views.py` add | Missing `action_description` raised `TypeError` (HTTP 500); non-numeric `action_type_id` raised `ValueError`. | Treated as empty description / unknown action. | `test_add_action_missing_description_is_allowed`, `test_add_action_validation_errors[abc]` |
| `aktionen/views.py` tracking | A `kilometerly_track` request with distance `0` or negative created actions with zero/negative climate points; any action id (not only trackable ones) could be booked; missing distance raised `TypeError`. | Distance must be a positive integer, action must have `track_kilometerly`. | `test_kilometer_tracking_rejects_invalid_distance`, `test_kilometer_tracking_only_for_trackable_actions` |
| `aktionen/views.py` `aktion_is_in_different_action_period` | `break` instead of `continue` when an action without time unit was encountered: remaining conflicting actions were ignored. | Skips only that action. | `test_later_non_timely_conflicting_action_is_skipped` |
| `users/views.py` `action_detail` edit | Daily maximum check used *today* instead of the action's date and counted the edited action itself (editing an action at the daily maximum always failed). | Uses the action's date and excludes the edited action. | `test_edit_action_max_check_uses_action_date_and_excludes_itself` |
| `users/views.py` `action_detail` edit | "Date too far in the past" redirected to the *add* page. | Redirects back to the action. | `test_edit_action_too_past_stays_on_action` |
| `users/views.py` notifications | English notification used the German level description on edit; level-up message had an unclosed `<span>`. | Shared message builder `utils/action_feedback.py`. | `test_edit_action_level_messages_use_matching_language` |
| `users/views.py` `report_user` | User supplied `reason` was inserted unescaped into the HTML mail to the admin (HTML injection); crashed when no user `admin` existed; blank reasons crashed (`NOT NULL`). | Escaped, tolerant of missing admin, blank reason rejected. | `test_report_user_escapes_reason`, `test_report_without_reason_is_rejected` |
| `users/views.py` `get_user` | Crashed for users without a `UserErweitert` profile. | Treated as "data not shared". | `test_get_user_without_profile` |

## Home / notifications

| File | Problem | Fix | Test |
|---|---|---|---|
| `home/views.py` `delete_benachrichtigung` | Any logged-in user could delete anybody's notification by id (missing permission check). | Only own notifications can be deleted. | `test_cannot_delete_notification_of_other_user` |
| `home/views.py` `admin` | Missing form fields raised `TypeError`; non-numeric event ids raised `ValueError`; community notifications were sent once *per family* of the user, so users in several families received duplicates. | Validation first; one notification per user. | `test_admin_missing_fields_does_not_crash`, `test_admin_errors[abc]`, `test_admin_family_community_and_event_receivers` |
| `home/views.py` `home` | Public landing page ran several queries *per user* of the whole site (and crashed for users without profile). | Three aggregate queries. | `test_home_query_count_is_independent_of_user_count` |
| `home/views.py` `dashboard` | Computed the worldwide rank with several queries per user of the site; crashed when the "worldwide ranking" family was missing. | Aggregate queries, `None` rank if the family is missing. | `test_dashboard_query_count_is_bounded`, `test_dashboard_without_worldwide_family` |
