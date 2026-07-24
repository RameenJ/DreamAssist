// frontend/lib/presentation/widgets/persona_widgets.dart

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/persona_models.dart';
import '../../presentation/providers/persona_provider.dart';

// ============================================================================
// PERSONA CARD - Interactive Selection Widget
// ============================================================================

class PersonaCard extends ConsumerWidget {
  final Persona persona;
  final bool isSelected;
  final VoidCallback onTap;
  final bool isLocked;

  const PersonaCard({
    Key? key,
    required this.persona,
    this.isSelected = false,
    required this.onTap,
    this.isLocked = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: isLocked ? null : onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected
                ? _hexToColor(persona.color)
                : Colors.grey.withOpacity(0.3),
            width: isSelected ? 3 : 1,
          ),
          color: isSelected
              ? _hexToColor(persona.color).withOpacity(0.1)
              : Colors.white,
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: _hexToColor(persona.color).withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  )
                ]
              : [],
        ),
        child: Stack(
          children: [
            // Main content
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Emoji avatar with glow effect
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _hexToColor(persona.color).withOpacity(0.15),
                      border: Border.all(
                        color: _hexToColor(persona.color).withOpacity(0.4),
                        width: 2,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        persona.emoji,
                        style: const TextStyle(fontSize: 48),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Name
                  Text(
                    persona.name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  // Description
                  Text(
                    persona.description,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 12),
                  // Unlock condition
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: isLocked
                          ? Colors.grey.withOpacity(0.2)
                          : _hexToColor(persona.color).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      isLocked ? '🔒 ${persona.unlockCondition}' : '✅ Unlocked',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: isLocked ? Colors.grey : _hexToColor(persona.color),
                            fontWeight: FontWeight.w500,
                          ),
                    ),
                  ),
                ],
              ),
            ),
            // Selected checkmark
            if (isSelected)
              Positioned(
                top: 12,
                right: 12,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _hexToColor(persona.color),
                  ),
                  child: const Icon(
                    Icons.check,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
            // Lock icon for locked personas
            if (isLocked)
              Positioned(
                top: 12,
                right: 12,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.grey.shade400,
                  ),
                  child: const Icon(
                    Icons.lock,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Color _hexToColor(String hex) {
    hex = hex.replaceFirst('#', '');
    return Color(int.parse(hex, radix: 16) + 0xFF000000);
  }
}

// ============================================================================
// PERSONA SELECTOR MODAL - Fun Selection Interface
// ============================================================================

class PersonaSelectorModal extends ConsumerWidget {
  final Function(String) onPersonaSelected;

  const PersonaSelectorModal({
    Key? key,
    required this.onPersonaSelected,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final allPersonasAsync = ref.watch(allPersonasProvider);
    final selectedPersona = ref.watch(selectedPersonaProvider);

    return allPersonasAsync.when(
      loading: () => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              'Loading personalities...',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
      error: (error, stack) => Center(
        child: Text('Error loading personas: $error'),
      ),
      data: (personas) {
        return SingleChildScrollView(
          child: Container(
            padding: EdgeInsets.only(
              top: 24,
              left: 16,
              right: 16,
              bottom: MediaQuery.of(context).viewInsets.bottom + 24,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '🧠 Choose Your Mentor',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Each mentor has a unique personality and teaching style',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                ),
                const SizedBox(height: 24),
                // Personas grid
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 1,
                    childAspectRatio: 1.0,
                    mainAxisSpacing: 16,
                  ),
                  itemCount: personas.length,
                  itemBuilder: (context, index) {
                    final persona = personas[index];
                    final isSelected = persona.personaId == selectedPersona;
                    final isLocked = !persona.isUnlocked;

                    return PersonaCard(
                      persona: persona,
                      isSelected: isSelected,
                      isLocked: isLocked,
                      onTap: () async {
                        // Select persona
                        await ref
                            .read(selectedPersonaProvider.notifier)
                            .selectPersona(persona.personaId);
                        
                        onPersonaSelected(persona.personaId);
                        
                        // Close modal
                        if (context.mounted) {
                          Navigator.pop(context);
                        }
                      },
                    );
                  },
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ============================================================================
// PERSONA HEADER - Display Current Persona
// ============================================================================

class PersonaHeader extends ConsumerWidget {
  final VoidCallback? onPersonaTap;

  const PersonaHeader({Key? key, this.onPersonaTap}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentPersonaAsync = ref.watch(currentPersonaProvider);

    return currentPersonaAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Center(
          child: CircularProgressIndicator(),
        ),
      ),
      error: (error, stack) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.red.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text('Error: $error'),
      ),
      data: (persona) {
        if (persona == null) {
          return const SizedBox.shrink();
        }

        return GestureDetector(
          onTap: onPersonaTap,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  _hexToColor(persona.color).withOpacity(0.2),
                  _hexToColor(persona.color).withOpacity(0.05),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: _hexToColor(persona.color).withOpacity(0.3),
              ),
            ),
            child: Row(
              children: [
                // Persona emoji
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _hexToColor(persona.color).withOpacity(0.15),
                  ),
                  child: Center(
                    child: Text(
                      persona.emoji,
                      style: const TextStyle(fontSize: 32),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Persona info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Chatting with',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey,
                            ),
                      ),
                      Text(
                        persona.name,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: _hexToColor(persona.color),
                            ),
                      ),
                    ],
                  ),
                ),
                // Change button
                Icon(
                  Icons.arrow_forward_ios,
                  size: 16,
                  color: _hexToColor(persona.color),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Color _hexToColor(String hex) {
    hex = hex.replaceFirst('#', '');
    return Color(int.parse(hex, radix: 16) + 0xFF000000);
  }
}
