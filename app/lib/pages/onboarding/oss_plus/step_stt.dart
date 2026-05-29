import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/l10n_extensions.dart';
import '_shared.dart';

class StepStt extends StatefulWidget {
  const StepStt({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepStt> createState() => _StepSttState();
}

class _StepSttState extends State<StepStt> {
  final _batchController = TextEditingController();
  final _streamController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _batchController.text = SharedPreferencesUtil().ossFasterWhisperBatchUrl;
    _streamController.text = SharedPreferencesUtil().ossFasterWhisperStreamUrl;
  }

  @override
  void dispose() {
    _batchController.dispose();
    _streamController.dispose();
    super.dispose();
  }

  bool get _canContinue => _batchController.text.trim().isNotEmpty && _streamController.text.trim().isNotEmpty;

  void _save() {
    SharedPreferencesUtil().ossFasterWhisperBatchUrl = _batchController.text.trim();
    SharedPreferencesUtil().ossFasterWhisperStreamUrl = _streamController.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'Faster-Whisper',
      subtitle: context.l10n.ossSpeechSubtitle,
      icon: Icons.mic,
      child: Column(
        children: [
          OssTextField(
            controller: _batchController,
            label: 'Batch URL',
            hint: 'http://localhost:8001',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _streamController,
            label: 'Streaming URL',
            hint: 'ws://localhost:8002',
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
