import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/backend/http/api/openrouter.dart';
import 'package:omi/utils/l10n_extensions.dart';
import 'package:omi/utils/logger.dart';
import '_shared.dart';

class StepLlmProvider extends StatefulWidget {
  const StepLlmProvider({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepLlmProvider> createState() => _StepLlmProviderState();
}

class _StepLlmProviderState extends State<StepLlmProvider> {
  String _selectedProvider = '';
  final _apiKeyController = TextEditingController();
  bool _keyVerified = false;
  bool _isLoading = false;
  List<OpenRouterModel> _llmModels = [];
  List<OpenRouterModel> _embeddingModels = [];
  String? _selectedLlmModel;
  String? _selectedEmbeddingModel;
  UsageInfo? _usageInfo;
  String? _error;

  @override
  void initState() {
    super.initState();
    _selectedProvider = SharedPreferencesUtil().ossLlmProvider;
    _apiKeyController.text = SharedPreferencesUtil().ossOpenrouterApiKey;
    _selectedLlmModel = SharedPreferencesUtil().ossOpenrouterLlmModel;
    _selectedEmbeddingModel = SharedPreferencesUtil().ossOpenrouterEmbeddingModel;

    if (_apiKeyController.text.isNotEmpty && _selectedProvider == 'openrouter') {
      _verifyKey();
    }
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  Future<void> _verifyKey() async {
    final key = _apiKeyController.text.trim();
    if (key.isEmpty) {
      setState(() => _error = 'API key is required');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final service = OpenRouterService(apiKey: key);
      final models = await service.listModels();

      if (models.isEmpty) {
        setState(() => _error = 'Failed to load models or invalid API key');
        return;
      }

      final usage = await service.getUsageInfo();
      final llmModels = models.where((m) => m.supportsCompletion()).toList();
      final embeddingModels = models.where((m) => m.supportsEmbeddings()).toList();

      setState(() {
        _llmModels = llmModels;
        _embeddingModels = embeddingModels;
        _usageInfo = usage;
        _keyVerified = true;
        _isLoading = false;

        if (_selectedLlmModel == null && _llmModels.isNotEmpty) {
          _selectedLlmModel = _llmModels.first.id;
        }
        if (_selectedEmbeddingModel == null && _embeddingModels.isNotEmpty) {
          _selectedEmbeddingModel = _embeddingModels.first.id;
        }
      });
    } catch (e) {
      Logger.error('OpenRouter verification error: $e');
      setState(() {
        _error = 'Failed to verify API key: $e';
        _isLoading = false;
      });
    }
  }

  void _save() {
    SharedPreferencesUtil().ossLlmProvider = _selectedProvider;
    if (_selectedProvider == 'openrouter') {
      SharedPreferencesUtil().ossOpenrouterApiKey = _apiKeyController.text.trim();
      if (_selectedLlmModel != null) {
        SharedPreferencesUtil().ossOpenrouterLlmModel = _selectedLlmModel!;
      }
      if (_selectedEmbeddingModel != null) {
        SharedPreferencesUtil().ossOpenrouterEmbeddingModel = _selectedEmbeddingModel!;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'AI Model',
      subtitle: 'Choose your LLM provider',
      icon: Icons.smart_toy,
      child: Column(
        children: [
          Text(
            'How do you want to run AI models?',
            style: TextStyle(fontSize: 16, color: Colors.grey[300]),
          ),
          const SizedBox(height: 24),

          // OpenRouter Option
          _ProviderCard(
            title: 'OpenRouter (Cloud)',
            description: 'Fast, latest models, no setup needed',
            icon: Icons.cloud,
            isSelected: _selectedProvider == 'openrouter',
            onSelect: () => setState(() {
              _selectedProvider = 'openrouter';
              if (_apiKeyController.text.isNotEmpty && !_keyVerified) {
                _verifyKey();
              }
            }),
          ),
          const SizedBox(height: 16),

          // OpenRouter Configuration
          if (_selectedProvider == 'openrouter') ...[
            if (_error != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.withOpacity(0.3)),
                ),
                child: Text(
                  _error!,
                  style: const TextStyle(color: Colors.red, fontSize: 13),
                ),
              ),
              const SizedBox(height: 16),
            ],

            OssTextField(
              controller: _apiKeyController,
              label: 'OpenRouter API Key',
              hint: 'sk-or-v1-...',
              obscure: !_keyVerified,
              optionalLabel: 'Get it from openrouter.ai/keys',
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              height: 44,
              child: ElevatedButton(
                onPressed: _isLoading || _apiKeyController.text.trim().isEmpty ? null : _verifyKey,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: Colors.blue.withOpacity(0.5),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Verify & Load Models', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(height: 24),

            if (_keyVerified) ...[
              if (_usageInfo != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.withOpacity(0.2)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Balance', style: TextStyle(fontSize: 12, color: Colors.white70)),
                      Text(
                        _usageInfo!.balanceFormatted,
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blue),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              Text(
                'LLM Model',
                style: TextStyle(fontSize: 12, color: Colors.grey[400], fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white.withOpacity(0.15)),
                ),
                child: DropdownButton<String>(
                  value: _selectedLlmModel,
                  isExpanded: true,
                  underline: const SizedBox(),
                  dropdownColor: Colors.grey[900],
                  items: _llmModels
                      .map((m) => DropdownMenuItem(
                            value: m.id,
                            child: Text(m.name, style: const TextStyle(color: Colors.white, fontSize: 13)),
                          ))
                      .toList(),
                  onChanged: (value) => setState(() => _selectedLlmModel = value),
                ),
              ),
              const SizedBox(height: 16),

              Text(
                'Embedding Model',
                style: TextStyle(fontSize: 12, color: Colors.grey[400], fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white.withOpacity(0.15)),
                ),
                child: DropdownButton<String>(
                  value: _selectedEmbeddingModel,
                  isExpanded: true,
                  underline: const SizedBox(),
                  dropdownColor: Colors.grey[900],
                  items: _embeddingModels
                      .map((m) => DropdownMenuItem(
                            value: m.id,
                            child: Text(m.name, style: const TextStyle(color: Colors.white, fontSize: 13)),
                          ))
                      .toList(),
                  onChanged: (value) => setState(() => _selectedEmbeddingModel = value),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ],

          // Ollama Option
          _ProviderCard(
            title: 'Ollama (Local)',
            description: 'Self-hosted, private, no cloud costs',
            icon: Icons.computer,
            isSelected: _selectedProvider == 'ollama',
            onSelect: () => setState(() => _selectedProvider = 'ollama'),
          ),
          const SizedBox(height: 32),

          // Continue Button
          OssNextButton(
            enabled: _selectedProvider.isNotEmpty &&
                (_selectedProvider == 'ollama' ||
                    (_keyVerified && _selectedLlmModel != null && _selectedEmbeddingModel != null)),
            label: context.l10n.continueButton,
            onPressed: () {
              _save();
              widget.onNext();
            },
          ),
        ],
      ),
    );
  }
}

class _ProviderCard extends StatelessWidget {
  const _ProviderCard({
    required this.title,
    required this.description,
    required this.icon,
    required this.isSelected,
    required this.onSelect,
  });

  final String title;
  final String description;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onSelect;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onSelect,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(
            color: isSelected ? Colors.blue : Colors.white12,
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(12),
          color: isSelected ? Colors.blue.withOpacity(0.1) : Colors.transparent,
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: isSelected ? Colors.blue : Colors.white.withOpacity(0.08),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: isSelected ? Colors.blue : Colors.white70),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                  ),
                ],
              ),
            ),
            if (isSelected)
              const Icon(Icons.check_circle, color: Colors.blue, size: 24),
          ],
        ),
      ),
    );
  }
}
