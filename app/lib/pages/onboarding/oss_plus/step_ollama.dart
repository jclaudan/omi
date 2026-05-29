import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/l10n_extensions.dart';
import '_shared.dart';

class StepOllama extends StatefulWidget {
  const StepOllama({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepOllama> createState() => _StepOllamaState();
}

class _StepOllamaState extends State<StepOllama> {
  final _urlController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _urlController.text = SharedPreferencesUtil().ossOllamaUrl;
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _save() {
    SharedPreferencesUtil().ossOllamaUrl = _urlController.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'Ollama',
      subtitle: context.l10n.ossLocalAiSubtitle,
      icon: Icons.psychology,
      child: Column(
        children: [
          OssTextField(
            controller: _urlController,
            label: 'URL',
            hint: 'http://localhost:11434',
            optionalLabel: context.l10n.ossOptional,
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 32),
          OssNextButton(
            enabled: true,
            label: context.l10n.continueButton,
            onPressed: () {
              _save();
              widget.onNext();
            },
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () {
              SharedPreferencesUtil().ossOllamaUrl = '';
              widget.onNext();
            },
            child: Text(context.l10n.skip, style: TextStyle(color: Colors.grey[500])),
          ),
        ],
      ),
    );
  }
}
