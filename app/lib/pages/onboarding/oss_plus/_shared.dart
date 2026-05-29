import 'package:flutter/material.dart';

/// Shared scaffold for each OSS+ onboarding step.
class OssStepScaffold extends StatelessWidget {
  const OssStepScaffold({
    super.key,
    required this.onBack,
    required this.serviceName,
    required this.subtitle,
    required this.icon,
    required this.child,
  });

  final VoidCallback onBack;
  final String serviceName;
  final String subtitle;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: onBack,
            child: const Icon(Icons.arrow_back_ios, color: Colors.white70, size: 20),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 24, color: Colors.white),
              ),
              const SizedBox(width: 14),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    serviceName,
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  Text(subtitle, style: TextStyle(fontSize: 14, color: Colors.grey[500])),
                ],
              ),
            ],
          ),
          const SizedBox(height: 32),
          Expanded(child: SingleChildScrollView(child: child)),
        ],
      ),
    );
  }
}

/// Styled text field for OSS+ forms.
class OssTextField extends StatelessWidget {
  const OssTextField({
    super.key,
    required this.controller,
    required this.label,
    required this.hint,
    this.obscure = false,
    this.optionalLabel,
    this.onChanged,
  });

  final TextEditingController controller;
  final String label;
  final String hint;
  final bool obscure;
  final String? optionalLabel;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label,
              style: const TextStyle(fontSize: 13, color: Colors.white70, fontWeight: FontWeight.w500),
            ),
            if (optionalLabel != null) ...[
              const SizedBox(width: 6),
              Text(optionalLabel!, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            ],
          ],
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          obscureText: obscure,
          onChanged: onChanged,
          style: const TextStyle(color: Colors.white, fontSize: 15),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: Colors.grey[600], fontSize: 14),
            filled: true,
            fillColor: Colors.white.withOpacity(0.06),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.white.withOpacity(0.15)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.white.withOpacity(0.15)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Colors.white54),
            ),
          ),
        ),
      ],
    );
  }
}

/// Primary action button for OSS+ steps.
class OssNextButton extends StatelessWidget {
  const OssNextButton({super.key, required this.enabled, required this.label, required this.onPressed});

  final bool enabled;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: enabled ? onPressed : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          disabledBackgroundColor: Colors.white24,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      ),
    );
  }
}
