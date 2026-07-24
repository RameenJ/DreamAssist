import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/subject_profile_provider.dart';
import '../../../core/theme/app_theme.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final profileState = ref.watch(subjectProfileProvider);

    // Load subject profiles when screen builds
    if (profileState.profiles.isEmpty && !profileState.isLoading) {
      Future.microtask(() => ref.read(subjectProfileProvider.notifier).loadProfiles());
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
      ),
      body: user == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // Profile avatar
                  CircleAvatar(
                    radius: 60,
                    backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.1),
                    child: Text(
                      user.firstname[0].toUpperCase() + user.lastname[0].toUpperCase(),
                      style: const TextStyle(
                        fontSize: 40,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryColor,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    user.fullName,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user.email,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppTheme.textSecondary,
                        ),
                  ),
                  const SizedBox(height: 32),

                  // Profile details
                  Card(
                    child: Column(
                      children: [
                        _ProfileItem(
                          icon: Icons.cake,
                          label: 'Age',
                          value: user.age?.toString() ?? 'N/A',
                        ),
                        const Divider(height: 1),
                        _ProfileItem(
                          icon: Icons.school,
                          label: 'University',
                          value: user.universityName ?? 'N/A',
                        ),
                        const Divider(height: 1),
                        _ProfileItem(
                          icon: Icons.verified_user,
                          label: 'Status',
                          value: user.verified ? 'Verified' : 'Not Verified',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // My Subjects section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'My Subjects',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      TextButton.icon(
                        onPressed: () => context.push('/preferences'),
                        icon: const Icon(Icons.edit),
                        label: const Text('Manage'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  if (profileState.isLoading)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: CircularProgressIndicator(),
                      ),
                    )
                  else if (profileState.profiles.isEmpty)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          children: [
                            Icon(
                              Icons.school_outlined,
                              size: 48,
                              color: AppTheme.textSecondary.withValues(alpha: 0.5),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'No subjects added yet',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppTheme.textSecondary,
                                  ),
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton.icon(
                              onPressed: () => context.push('/preferences'),
                              icon: const Icon(Icons.add),
                              label: const Text('Add Subjects'),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    ...profileState.profiles.map((profile) => Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: _getLevelColor(profile.level).withValues(alpha: 0.2),
                              child: Icon(
                                _getLevelIcon(profile.level),
                                color: _getLevelColor(profile.level),
                              ),
                            ),
                            title: Text(
                              profile.subject,
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Text(
                              '${profile.level.toUpperCase()} • ${profile.studyPace} pace',
                              style: const TextStyle(color: AppTheme.textSecondary),
                            ),
                            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                            onTap: () => context.push('/preferences'),
                          ),
                        )),

                  const SizedBox(height: 24),

                  // Logout button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        await ref.read(authProvider.notifier).logout();
                        if (context.mounted) {
                          context.go('/login');
                        }
                      },
                      icon: const Icon(Icons.logout),
                      label: const Text('Logout'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.errorColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  IconData _getLevelIcon(String level) {
    switch (level) {
      case 'beginner':
        return Icons.star_border;
      case 'intermediate':
        return Icons.star_half;
      case 'advanced':
        return Icons.star;
      default:
        return Icons.star_outline;
    }
  }

  Color _getLevelColor(String level) {
    switch (level) {
      case 'beginner':
        return Colors.green;
      case 'intermediate':
        return Colors.orange;
      case 'advanced':
        return Colors.red;
      default:
        return AppTheme.textSecondary;
    }
  }
}

class _ProfileItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ProfileItem({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.primaryColor),
      title: Text(label),
      trailing: Text(
        value,
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
    );
  }
}
