import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/backend/schema/app_mode.dart';
import 'package:omi/pages/onboarding/oss_plus/wrapper.dart';
import 'package:omi/pages/onboarding/wrapper.dart';
import 'package:omi/utils/l10n_extensions.dart';

class ModeSelectorPage extends StatefulWidget {
  const ModeSelectorPage({super.key});

  @override
  State<ModeSelectorPage> createState() => _ModeSelectorPageState();
}

class _ModeSelectorPageState extends State<ModeSelectorPage> {
  AppMode? _selected;

  void _select(AppMode mode) => setState(() => _selected = mode);

  void _continue() {
    if (_selected == null) return;
    SharedPreferencesUtil().appMode = _selected!;
    final page = _selected == AppMode.opensourcePlus ? const OssPlusOnboardingWrapper() : const OnboardingWrapper();
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Spacer(),
              Text(
                context.l10n.modeSelectorTitle,
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 8),
              Text('Omi', style: TextStyle(fontSize: 16, color: Colors.grey[500])),
              const SizedBox(height: 48),
              _ModeCard(
                title: context.l10n.officialModeTitle,
                description: context.l10n.officialModeDescription,
                selected: _selected == AppMode.official,
                onTap: () => _select(AppMode.official),
              ),
              const SizedBox(height: 16),
              _ModeCard(
                title: context.l10n.opensourcePlusModeTitle,
                description: context.l10n.opensourcePlusModeDescription,
                selected: _selected == AppMode.opensourcePlus,
                onTap: () => _select(AppMode.opensourcePlus),
              ),
              const Spacer(flex: 2),
              AnimatedOpacity(
                opacity: _selected != null ? 1.0 : 0.4,
                duration: const Duration(milliseconds: 200),
                child: SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _selected != null ? _continue : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black,
                      disabledBackgroundColor: Colors.white24,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: Text(
                      context.l10n.continueButton,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  const _ModeCard({required this.title, required this.description, required this.selected, required this.onTap});

  final String title;
  final String description;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: selected ? Colors.white.withOpacity(0.12) : Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: selected ? Colors.white : Colors.white24, width: selected ? 2 : 1),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.white),
                  ),
                  const SizedBox(height: 6),
                  Text(description, style: TextStyle(fontSize: 14, color: Colors.grey[400])),
                ],
              ),
            ),
            const SizedBox(width: 12),
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: selected ? Colors.white : Colors.transparent,
                border: Border.all(color: selected ? Colors.white : Colors.white54, width: 2),
              ),
              child: selected ? const Icon(Icons.check, size: 14, color: Colors.black) : null,
            ),
          ],
        ),
      ),
    );
  }
}
