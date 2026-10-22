---
schema_version: 1
id: CLAR-0002
task_id: REQ-0044
status: answered
source_artifacts:
  - .factory-state/artifacts/REQ-0044-chat-triggers.md
  - .factory-state/decisions/DEC-0019-approval-channels.md
  - .factory-state/decisions/DEC-0036-scheduled-runs.md
created: 2026-10-22
updated: 2026-10-22
answered_at: '2026-10-22'
questions:
  - id: who-may-run
    type: single_choice
    prompt: Who may start a run from a chat?
    required: true
    context: >-
      Chat accounts can already be linked to studio users with a code the bot sends (identity linking, used by
      approvals). A run always uses the workflow owner's credentials (DEC-0023), so anyone who may trigger it spends
      the owner's model budget. "Anyone in the chat" is easier to adopt, but then anyone invited to the Slack channel
      or Telegram group can start runs.
    recommendation: linked
    options:
      - value: linked
        label: Only people with a verified linked chat account whose studio user may run the workflow; the run is theirs
      - value: anyone
        label: Anyone who can write in the chosen chat; the run belongs to the trigger's creator and records the sender
    depends_on: null
  - id: routing
    type: single_choice
    prompt: How does a message pick its workflow?
    required: true
    context: >-
      One bot serves many workflows. A command word lets several workflows share a channel and the bot's direct
      messages. A dedicated chat is simpler to type in but needs one channel or group per workflow. Slack slash
      commands look native, but each command must be added in the Slack app settings, and Telegram has no equivalent
      in groups.
    recommendation: command-word
    options:
      - value: command-word
        label: "A command word: '@bot leave <text>' in a channel or group, 'leave <text>' in a direct message"
      - value: whole-chat
        label: Every message in the chosen channel or group (mentioning the bot) runs one workflow
      - value: slash-command
        label: "Slack slash command '/superstep leave <text>' (plus the command word on Telegram)"
    depends_on: null
  - id: reply
    type: single_choice
    prompt: What does the bot reply when the run ends?
    required: true
    context: >-
      The reply is posted in the thread for everyone in the chat to see. The final state can hold data the chat
      should not see; a chosen field keeps the reply short and deliberate.
    recommendation: field
    options:
      - value: field
        label: The value of one state field chosen on the trigger, with a link to the run
      - value: link-only
        label: Only the status (finished, error, waiting) and a link to the run
      - value: final-state
        label: The whole final state as JSON, shortened, with a link
    depends_on: null
  - id: input
    type: single_choice
    prompt: How does the message become run input?
    required: true
    context: >-
      Most workflows read one text field (request, question, feedback). Key=value pairs allow several fields, but
      people type them wrongly in a chat.
    recommendation: one-field
    options:
      - value: one-field
        label: The text after the command word goes into one input field chosen on the trigger
      - value: key-value
        label: Same, plus optional 'field=value' pairs that fill other input fields
    depends_on: null
answers:
  who-may-run: linked
  routing: command-word
  reply: field
  input: one-field
---
# Clarification

Owner questions for REQ-0044 (chat triggers). The owner answered all four in chat on 2026-10-22 and picked the
recommended option each time; the answers are written into REQ-0044.

The owner may answer it with:

```text
factory clarify CLAR-0002 -C <project-dir>
```

The implementing agent must propagate submitted answers into the related requirement, design, architecture, decision, or task artifacts.
