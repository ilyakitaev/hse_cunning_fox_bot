# Test Cases for Unit Tests

## Test Business Logic

### Authentication (TestAuth)
- `test_check_auth_unauthorized_user` - Verify check_auth returns False for unauthorized user
- `test_check_auth_authorized_user` - Verify check_auth returns True for authorized user
- `test_authorize_user` - Verify authorize_user calls database function
- `test_get_authorized_users` - Verify get_authorized_users returns empty list

### Public Commands (TestPublicCommands)
- `test_cmd_start` - Verify /start sends welcome message
- `test_cmd_auth_success` - Verify /auth with correct password authorizes user
- `test_cmd_auth_failure` - Verify /auth with wrong password shows error
- `test_cmd_list_assistants_empty` - Verify /assistants shows "no assistants" when empty
- `test_cmd_list_assistants_with_data` - Verify /assistants lists existing assistants

### Private Commands (TestPrivateCommands)
- `test_cmd_database_list_empty` - Verify /collections shows "no databases" when empty
- `test_cmd_database_list_with_data` - Verify /collections lists existing databases
- `test_cmd_database_create_success` - Verify /collection-create creates collection
- `test_cmd_database_create_failure` - Verify /collection-create shows error on failure
- `test_cmd_prompt_list_empty` - Verify /prompts shows "no prompts" when empty
- `test_cmd_prompt_list_with_data` - Verify /prompts lists existing prompts
- `test_cmd_prompt_create` - Verify /prompt-create creates new prompt
- `test_cmd_prompt_show_exists_by_id` - Verify /prompt-show displays prompt content by ID
- `test_cmd_prompt_show_exists_by_name` - Verify /prompt-show displays prompt content by name
- `test_cmd_prompt_show_not_found` - Verify /prompt-show shows error for invalid ID or name
- `test_cmd_prompt_update_success` - Verify /prompt-update updates prompt
- `test_cmd_prompt_update_not_found` - Verify /prompt-update shows error for invalid ID

### Assistant Interaction (TestAssistantInteraction)
- `test_query_assistant_success` - Verify querying assistant returns LLM response
- `test_query_assistant_not_found` - Verify error shown for invalid assistant ID
- `test_query_assistant_invalid_id` - Verify error shown for non-numeric assistant ID

### Help Command (TestHelpCommand)
- `test_cmd_help_success` - Verify /help sends content from help.md
- `test_cmd_help_file_not_found` - Verify /help handles missing file gracefully

### Assistant Create (TestAssistantCreateCommand)
- `test_cmd_assistant_create_success` - Verify /assistant-create creates assistant
- `test_cmd_assistant_create_invalid_collection` - Verify error for invalid collection
- `test_cmd_assistant_create_invalid_prompt` - Verify error for invalid prompt
- `test_cmd_assistant_create_interactive_start` - Verify /assistant-create starts interactive mode
- `test_handle_assistant_create_response_name` - Verify handling name in interactive mode
- `test_handle_assistant_create_response_collection` - Verify handling collection in interactive mode
- `test_handle_assistant_create_response_prompt` - Verify handling prompt and creating assistant
- `test_cancel_assistant_create` - Verify cancelling assistant creation

### Assist Command (TestAssistCommand)
- `test_cmd_assist_select_assistant` - Verify /assist selects an assistant
- `test_cmd_assist_show_current` - Verify /assist shows current selection
- `test_cmd_assist_not_found` - Verify error for invalid assistant name
- `test_get_selected_assistant` - Verify getting selected assistant
- `test_clear_selected_assistant` - Verify clearing selected assistant

### Unauthorized Access (TestUnauthorizedAccess)
- `test_database_list_unauthorized` - Verify /collections requires auth
- `test_database_create_unauthorized` - Verify /collection-create requires auth
- `test_prompt_list_unauthorized` - Verify /prompts requires auth
- `test_prompt_create_unauthorized` - Verify /prompt-create requires auth
- `test_prompt_show_unauthorized` - Verify /prompt-show requires auth
- `test_prompt_update_unauthorized` - Verify /prompt-update requires auth
- `test_assistant_create_unauthorized` - Verify /assistant-create requires auth

## Test API

### Telegram API (TestTelegramAPI)
- `test_send_telegram_message_success` - Verify successful message sending
- `test_send_telegram_message_failure` - Verify error handling on failure
- `test_send_telegram_message_no_token` - Verify no token returns False
- `test_set_webhook_success` - Verify webhook setting
- `test_delete_webhook_success` - Verify webhook deletion

### LLM API (TestLLMAPI)
- `test_call_llm_success` - Verify successful LLM call
- `test_call_llm_failure` - Verify error handling on failure
- `test_call_llm_no_apikey` - Verify no API key returns None

### Qdrant API (TestQdrantAPI)
- `test_create_collection_success` - Verify collection creation
- `test_create_collection_failure` - Verify error handling
- `test_delete_collection_success` - Verify collection deletion
- `test_list_collections_success` - Verify listing collections
- `test_list_collections_failure` - Verify error handling
- `test_add_to_collection_success` - Verify adding data to collection
- `test_add_to_collection_failure` - Verify error handling
- `test_search_collection_success` - Verify search returns results
- `test_search_collection_failure` - Verify error handling

### Embedding API (TestEmbeddingAPI)
- `test_get_embeddings_empty_texts` - Verify empty input returns empty list
- `test_get_embeddings_with_text` - Verify embedding generation

### Data Management Commands (TestDataCommands)
- `test_cmd_data_list_empty` - Verify /data_list shows "no records" when empty
- `test_cmd_data_list_with_data` - Verify /data_list lists existing records
- `test_cmd_data_show_exists` - Verify /data_show displays record content
- `test_cmd_data_show_not_found` - Verify /data_show shows error for invalid ID
- `test_cmd_data_remove_success` - Verify /data_remove deletes record
- `test_cmd_data_remove_not_found` - Verify /data_remove shows error for invalid ID
- `test_cmd_data_remove_all_success` - Verify /data_remove_all deletes all records
- `test_cmd_data_add_bulk_start` - Verify /data_add_bulk starts interactive mode
- `test_data_list_unauthorized` - Verify /data_list requires auth
- `test_data_show_unauthorized` - Verify /data_show requires auth
- `test_data_remove_unauthorized` - Verify /data_remove requires auth
- `test_data_remove_all_unauthorized` - Verify /data_remove_all requires auth
- `test_data_add_bulk_unauthorized` - Verify /data_add_bulk requires auth

### Qdrant Point Operations (TestQdrantPointsAPI)
- `test_list_points_success` - Verify listing points in collection
- `test_list_points_failure` - Verify error handling
- `test_get_point_success` - Verify getting single point
- `test_get_point_not_found` - Verify not found handling
- `test_delete_point_success` - Verify deleting single point
- `test_delete_point_failure` - Verify error handling
- `test_delete_all_points_success` - Verify deleting all points
- `test_delete_all_points_failure` - Verify error handling

### Assistant Query (TestAssistantQuery)
- `test_query_assistant_with_selected` - Verify querying assistant with selected assistant
- `test_get_selected_assistant_from_state` - Verify getting selected assistant from state

### Integration: End-to-End Assistant Flow (TestAssistantFlow)
- `test_full_assistant_flow` - Test: select assistant -> send message -> get response
