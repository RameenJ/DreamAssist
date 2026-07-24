// lib/screens/conflict_detection_screen.dart
// Multi-Plan Conflict Detection UI (Phase 2c)

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class ConflictDetectionScreen extends StatefulWidget {
  const ConflictDetectionScreen({super.key});

  @override
  State<ConflictDetectionScreen> createState() => _ConflictDetectionScreenState();
}

class _ConflictDetectionScreenState extends State<ConflictDetectionScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoadingConflicts = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _detectConflicts();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _detectConflicts() {
    setState(() => _isLoadingConflicts = true);
    // Simulate API call
    Future.delayed(const Duration(seconds: 2), () {
      setState(() => _isLoadingConflicts = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Conflict Detection'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _detectConflicts,
            tooltip: 'Refresh',
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Conflicts'),
            Tab(text: 'Dashboard'),
          ],
        ),
      ),
      body: _isLoadingConflicts
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: const [
                ConflictsListTab(),
                ConflictDashboardTab(),
              ],
            ),
    );
  }
}

// ========================================================================
// CONFLICTS LIST TAB
// ========================================================================

class ConflictsListTab extends StatefulWidget {
  const ConflictsListTab({super.key});

  @override
  State<ConflictsListTab> createState() => _ConflictsListTabState();
}

class _ConflictsListTabState extends State<ConflictsListTab> {
  String _selectedFilter = 'unresolved';

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Filter Chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              FilterChip(
                label: const Text('Unresolved'),
                selected: _selectedFilter == 'unresolved',
                onSelected: (s) => setState(() => _selectedFilter = 'unresolved'),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Resolved'),
                selected: _selectedFilter == 'resolved',
                onSelected: (s) => setState(() => _selectedFilter = 'resolved'),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('All'),
                selected: _selectedFilter == 'all',
                onSelected: (s) => setState(() => _selectedFilter = 'all'),
              ),
            ],
          ),
        ),

        // Conflicts List
        Expanded(
          child: _selectedFilter == 'unresolved'
              ? _buildUnresolvedConflictsList()
              : _buildResolvedConflictsList(),
        ),

        // Auto-Resolve Button
        if (_selectedFilter != 'resolved')
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _showAutoResolveDialog,
                icon: const Icon(Icons.auto_fix_high),
                label: const Text('Auto-Resolve All'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildUnresolvedConflictsList() {
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      children: [
        ConflictCard(
          conflictType: 'Time Overlap',
          severity: 'high',
          description: 'DSA Study and Web Dev Study scheduled on same day',
          affectedPlans: const ['DSA Study Plan', 'Web Dev Plan'],
          affectedHours: 4.0,
          conflictDate: '2025-01-20',
          onTap: () => _showConflictDetails(context),
          onResolve: () => _showResolutionSuggestions(context),
        ),
        const SizedBox(height: 12),
        ConflictCard(
          conflictType: 'Resource Exhaustion',
          severity: 'high',
          description: 'Total study load exceeds 8 hours on this date',
          affectedPlans: const ['Phase 2 Study', 'Interview Prep', 'DSA Bootcamp'],
          affectedHours: 10.5,
          conflictDate: '2025-01-22',
          onTap: () => _showConflictDetails(context),
          onResolve: () => _showResolutionSuggestions(context),
        ),
        const SizedBox(height: 12),
        ConflictCard(
          conflictType: 'Priority Clash',
          severity: 'medium',
          description: 'Multiple plans for Data Structures subject',
          affectedPlans: const ['DSA Study Plan', 'Interview DSA Prep'],
          affectedHours: 8.0,
          conflictDate: '2025-01-18',
          onTap: () => _showConflictDetails(context),
          onResolve: () => _showResolutionSuggestions(context),
        ),
      ],
    );
  }

  Widget _buildResolvedConflictsList() {
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      children: [
        ConflictCard(
          conflictType: 'Time Overlap',
          severity: 'high',
          description: 'DSA Study and Web Dev Study scheduled on same day',
          affectedPlans: const ['DSA Study Plan', 'Web Dev Plan'],
          affectedHours: 4.0,
          conflictDate: '2025-01-15',
          isResolved: true,
          resolutionType: 'Rescheduled',
          onTap: () => _showConflictDetails(context),
        ),
        const SizedBox(height: 12),
        ConflictCard(
          conflictType: 'Resource Exhaustion',
          severity: 'medium',
          description: 'Study hours exceeded on multiple days',
          affectedPlans: const ['Study Plan A', 'Study Plan B'],
          affectedHours: 6.0,
          conflictDate: '2025-01-10',
          isResolved: true,
          resolutionType: 'Extended Deadline',
          onTap: () => _showConflictDetails(context),
        ),
      ],
    );
  }

  void _showAutoResolveDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Auto-Resolve Conflicts'),
        content: const Text(
          'This will automatically resolve all conflicts using the best suggestions. Continue?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Resolved 3 conflicts!')),
              );
            },
            child: const Text('Resolve'),
          ),
        ],
      ),
    );
  }
}

// ========================================================================
// CONFLICT CARD WIDGET
// ========================================================================

class ConflictCard extends StatelessWidget {
  final String conflictType;
  final String severity;
  final String description;
  final List<String> affectedPlans;
  final double affectedHours;
  final String conflictDate;
  final bool isResolved;
  final String? resolutionType;
  final VoidCallback onTap;
  final VoidCallback? onResolve;

  const ConflictCard({
    super.key,
    required this.conflictType,
    required this.severity,
    required this.description,
    required this.affectedPlans,
    required this.affectedHours,
    required this.conflictDate,
    this.isResolved = false,
    this.resolutionType,
    required this.onTap,
    this.onResolve,
  });

  @override
  Widget build(BuildContext context) {
    final severityColor = _getSeverityColor();

    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 4,
                    height: 60,
                    color: severityColor,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              conflictType,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Chip(
                              label: Text(
                                severity.toUpperCase(),
                                style: const TextStyle(fontSize: 10),
                              ),
                              backgroundColor: severityColor.withOpacity(0.2),
                              side: BorderSide(color: severityColor),
                              padding: const EdgeInsets.symmetric(horizontal: 8),
                            ),
                            const SizedBox(width: 8),
                            if (isResolved)
                              Chip(
                                label: const Text(
                                  'RESOLVED',
                                  style: TextStyle(fontSize: 10),
                                ),
                                backgroundColor: Colors.green.withOpacity(0.2),
                                side: const BorderSide(color: Colors.green),
                                padding: const EdgeInsets.symmetric(horizontal: 8),
                              ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          description,
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Affected Plans
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Affected Plans (${affectedPlans.length})',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 4,
                    children: affectedPlans
                        .map((plan) => Chip(
                              label: Text(plan, style: const TextStyle(fontSize: 11)),
                              visualDensity: VisualDensity.compact,
                            ))
                        .toList(),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Stats Row
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Affected Hours',
                        style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                      ),
                      Text(
                        '${affectedHours.toStringAsFixed(1)} hrs',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        'Conflict Date',
                        style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                      ),
                      Text(
                        DateFormat('MMM d, yyyy').format(
                          DateTime.parse(conflictDate),
                        ),
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),

              // Resolution Info
              if (isResolved && resolutionType != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.check_circle,
                          size: 16,
                          color: Colors.green,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Resolved by: $resolutionType',
                          style: const TextStyle(fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ),

              // Action Buttons
              if (!isResolved && onResolve != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: onResolve,
                      icon: const Icon(Icons.lightbulb_outline, size: 18),
                      label: const Text('View Solutions'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue.shade600,
                        padding: const EdgeInsets.symmetric(vertical: 8),
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

  Color _getSeverityColor() {
    switch (severity.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.yellow;
      default:
        return Colors.grey;
    }
  }
}

// ========================================================================
// CONFLICT DETAILS SHEET
// ========================================================================

void _showConflictDetails(BuildContext context) {
  showModalBottomSheet(
    context: context,
    builder: (context) => Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Conflict Analysis',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Conflict Type: Time Overlap',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'Severity: HIGH',
            style: TextStyle(color: Colors.red),
          ),
          const SizedBox(height: 16),
          const Text(
            'Description:',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text(
            'Your DSA Study Plan and Web Development Study Plan are both scheduled for 2025-01-20. This creates a time conflict of 4 hours.',
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ),
        ],
      ),
    ),
  );
}

// ========================================================================
// RESOLUTION SUGGESTIONS SHEET
// ========================================================================

void _showResolutionSuggestions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    builder: (context) => Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Resolution Suggestions',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView(
              children: [
                ResolutionSuggestionTile(
                  title: 'Reschedule DSA Study',
                  description: 'Move DSA study to 2025-01-21',
                  confidence: 0.85,
                  impact: -0.3,
                  onApply: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Conflict resolved!')),
                    );
                  },
                ),
                const SizedBox(height: 12),
                ResolutionSuggestionTile(
                  title: 'Merge Study Sessions',
                  description: 'Combine related topics and study together',
                  confidence: 0.65,
                  impact: 0.2,
                  onApply: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Sessions merged!')),
                    );
                  },
                ),
                const SizedBox(height: 12),
                ResolutionSuggestionTile(
                  title: 'Redistribute Hours',
                  description: 'Spread study hours across more days',
                  confidence: 0.75,
                  impact: 0.1,
                  onApply: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Hours redistributed!')),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}

class ResolutionSuggestionTile extends StatelessWidget {
  final String title;
  final String description;
  final double confidence;
  final double impact;
  final VoidCallback onApply;

  const ResolutionSuggestionTile({
    super.key,
    required this.title,
    required this.description,
    required this.confidence,
    required this.impact,
    required this.onApply,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              description,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Confidence: ${(confidence * 100).toInt()}%',
                      style: const TextStyle(fontSize: 11),
                    ),
                    Text(
                      'Impact: ${impact > 0 ? '+' : ''}${(impact * 100).toInt()}%',
                      style: TextStyle(
                        fontSize: 11,
                        color: impact > 0 ? Colors.green : Colors.orange,
                      ),
                    ),
                  ],
                ),
                ElevatedButton(
                  onPressed: onApply,
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 16)),
                  child: const Text('Apply'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ========================================================================
// CONFLICT DASHBOARD TAB
// ========================================================================

class ConflictDashboardTab extends StatelessWidget {
  const ConflictDashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: const [
        // Summary Cards
        SummaryCard(
          title: 'Total Conflicts',
          value: '5',
          icon: Icons.warning_rounded,
          color: Colors.red,
        ),
        SizedBox(height: 12),
        SummaryCard(
          title: 'Unresolved',
          value: '2',
          icon: Icons.pending_actions,
          color: Colors.orange,
        ),
        SizedBox(height: 12),
        SummaryCard(
          title: 'Resolved',
          value: '3',
          icon: Icons.check_circle,
          color: Colors.green,
        ),
        SizedBox(height: 12),
        SummaryCard(
          title: 'Affected Hours',
          value: '14.5',
          icon: Icons.timer,
          color: Colors.blue,
        ),
        SizedBox(height: 24),

        // Conflict Type Breakdown
        Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Conflict Types',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 16),
                _ConflictTypeRow(
                  label: 'Time Overlap',
                  count: 2,
                  percentage: 40,
                ),
                SizedBox(height: 12),
                _ConflictTypeRow(
                  label: 'Resource Exhaustion',
                  count: 2,
                  percentage: 40,
                ),
                SizedBox(height: 12),
                _ConflictTypeRow(
                  label: 'Priority Clash',
                  count: 1,
                  percentage: 20,
                ),
              ],
            ),
          ),
        ),
        SizedBox(height: 24),

        // Severity Breakdown
        Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Severity Breakdown',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 16),
                _SeverityRow(
                  label: 'High',
                  count: 3,
                  color: Colors.red,
                ),
                SizedBox(height: 12),
                _SeverityRow(
                  label: 'Medium',
                  count: 2,
                  color: Colors.orange,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class SummaryCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const SummaryCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConflictTypeRow extends StatelessWidget {
  final String label;
  final int count;
  final double percentage;

  const _ConflictTypeRow({
    required this.label,
    required this.count,
    required this.percentage,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12)),
            Text('$count conflicts', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 4),
        LinearProgressIndicator(
          value: percentage / 100,
          minHeight: 6,
          backgroundColor: Colors.grey[200],
        ),
      ],
    );
  }
}

class _SeverityRow extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _SeverityRow({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 12),
        Text(label, style: const TextStyle(fontSize: 12)),
        const Spacer(),
        Text(
          '$count',
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}
