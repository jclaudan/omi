import 'package:flutter/material.dart';
import 'package:omi/utils/l10n_extensions.dart';

class StepWelcome extends StatelessWidget {
  const StepWelcome({super.key, required this.onNext});

  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Spacer(),
          const Text('⚙️', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 24),
          Text(
            context.l10n.ossSetupTitle,
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Text(context.l10n.ossSetupWelcomeBody, style: TextStyle(fontSize: 16, color: Colors.grey[400], height: 1.5)),
          const SizedBox(height: 32),
          _ServiceRow(icon: Icons.security, label: 'Supabase', subtitle: context.l10n.ossAuthSubtitle),
          _ServiceRow(icon: Icons.mic, label: 'Faster-Whisper', subtitle: context.l10n.ossSpeechSubtitle),
          _ServiceRow(icon: Icons.hub, label: 'Qdrant', subtitle: context.l10n.ossVectorSubtitle),
          _ServiceRow(icon: Icons.storage, label: 'MinIO', subtitle: context.l10n.ossStorageSubtitle),
          _ServiceRow(icon: Icons.psychology, label: 'Ollama', subtitle: context.l10n.ossLocalAiSubtitle),
          const Spacer(flex: 2),
          _NextButton(onPressed: onNext, label: context.l10n.continueButton),
        ],
      ),
    );
  }
}

class _ServiceRow extends StatelessWidget {
  const _ServiceRow({required this.icon, required this.label, required this.subtitle});

  final IconData icon;
  final String label;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.08), borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, size: 20, color: Colors.white70),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white),
              ),
              Text(subtitle, style: TextStyle(fontSize: 13, color: Colors.grey[500])),
            ],
          ),
        ],
      ),
    );
  }
}

class _NextButton extends StatelessWidget {
  const _NextButton({required this.onPressed, required this.label});

  final VoidCallback onPressed;
  final String label;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      ),
    );
  }
}
