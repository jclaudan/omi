import 'dart:convert';

import 'package:omi/backend/http/shared.dart';
import 'package:omi/env/env.dart';

/// Configure OSS+ LLM provider preference.
///
/// Saves the user's choice of LLM provider (openrouter, ollama, or custom) and configuration.
Future<bool> configureOssLlmProvider({
  required String provider,
  String? openrouterApiKey,
  String? openrouterLlmModel,
  String? openrouterEmbeddingModel,
  String? customProviderUrl,
  String? customProviderModel,
}) async {
  final url = '${Env.apiBaseUrl}v1/oss/configure-llm';

  final Map<String, dynamic> bodyMap = {
    'provider': provider,
  };

  if (provider == 'openrouter') {
    if (openrouterApiKey != null) {
      bodyMap['openrouter'] = {
        'api_key': openrouterApiKey,
        if (openrouterLlmModel != null) 'llm_model': openrouterLlmModel,
        if (openrouterEmbeddingModel != null) 'embedding_model': openrouterEmbeddingModel,
      };
    }
  } else if (provider == 'custom') {
    if (customProviderUrl != null && customProviderModel != null) {
      bodyMap['custom'] = {
        'base_url': customProviderUrl,
        'model': customProviderModel,
      };
    }
  }

  final body = jsonEncode(bodyMap);

  try {
    var res = await makeApiCall(
      url: url,
      headers: {'Content-Type': 'application/json'},
      body: body,
      method: 'POST',
    );

    if (res == null || res.statusCode != 200) {
      return false;
    }

    final data = jsonDecode(res.body);
    return data['success'] == true;
  } catch (e) {
    return false;
  }
}

/// Get the current OSS+ LLM configuration.
Future<String?> getOssLlmProvider() async {
  final url = '${Env.apiBaseUrl}v1/oss/llm-config';

  try {
    var res = await makeApiCall(url: url, headers: {}, body: '', method: 'GET');

    if (res == null || res.statusCode != 200) {
      return null;
    }

    final data = jsonDecode(res.body);
    return data['provider'] as String?;
  } catch (e) {
    return null;
  }
}
