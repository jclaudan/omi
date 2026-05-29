import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/l10n_extensions.dart';
import '_shared.dart';

class StepQdrant extends StatefulWidget {
  const StepQdrant({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepQdrant> createState() => _StepQdrantState();
}

class _StepQdrantState extends State<StepQdrant> {
  final _urlController = TextEditingController();
  final _apiKeyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _urlController.text = SharedPreferencesUtil().ossQdrantUrl;
    _apiKeyController.text = SharedPreferencesUtil().ossQdrantApiKey;
  }

  @override
  void dispose() {
    _urlController.dispose();
    _apiKeyController.dispose();
    super.dispose();
  }

  bool get _canContinue => _urlController.text.trim().isNotEmpty;

  void _save() {
    SharedPreferencesUtil().ossQdrantUrl = _urlController.text.trim();
    SharedPreferencesUtil().ossQdrantApiKey = _apiKeyController.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'Qdrant',
      subtitle: context.l10n.ossVectorSubtitle,
      icon: Icons.hub,
      child: Column(
        children: [
          OssTextField(
            controller: _urlController,
            label: 'URL',
            hint: 'http://localhost:6333',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _apiKeyController,
            label: 'API Key',
            hint: '',
            obscure: true,
            optionalLabel: context.l10n.ossOptional,
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 32),
          OssNextButton(
            enabled: _canContinue,
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
