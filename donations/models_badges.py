from django.conf import settings
from django.db import models


class Badge(models.TextChoices):
    """Badge types for donor achievements"""
    FIRST_DONATION = "first_donation", "First Donation"
    FIVE_DONATIONS = "five_donations", "5 Donations"
    TEN_DONATIONS = "ten_donations", "10 Donations"
    HERO = "hero", "Blood Hero (20+ Donations)"
    LIFESAVER = "lifesaver", "Lifesaver (30+ Donations)"
    CONSISTENT = "consistent", "Consistent Donor (Donated 6+ months consecutively)"
    EMERGENCY_RESPONDER = "emergency", "Emergency Responder (Responded to 3+ SOS)"
    TRUSTED_DONOR = "trusted", "Trusted Donor (5+ positive confirmations)"
    SPEED_DONOR = "speed", "Speed Donor (Responded to SOS within 1 hour)"


class DonorStatistics(models.Model):
    """Track donor achievements, badges, and statistics"""
    
    donor = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="donor_stats")
    total_donations = models.PositiveIntegerField(default=0)
    total_lives_saved = models.PositiveIntegerField(default=0)
    sos_responses = models.PositiveIntegerField(default=0)
    successful_sos_responses = models.PositiveIntegerField(default=0)
    badges = models.JSONField(default=list, help_text="List of badge types earned")
    rank = models.PositiveIntegerField(default=0, help_text="Leaderboard rank")
    points = models.PositiveIntegerField(default=0, help_text="Accumulated points for achievements")
    
    # Streak tracking
    current_donation_streak = models.PositiveIntegerField(default=0, help_text="Months of consecutive donations")
    last_donation_streak_date = models.DateField(null=True, blank=True)
    
    # Engagement
    response_rate = models.FloatField(default=0.0, help_text="SOS response acceptance rate (0-100)")
    average_response_time_hours = models.FloatField(default=0.0, help_text="Average hours to respond to SOS")
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Donor Statistics"
        ordering = ['-points', '-total_donations']

    def __str__(self) -> str:
        return f"{self.donor.username} - {self.total_donations} donations"

    def check_badges(self):
        """Automatically award badges based on statistics"""
        new_badges = []
        
        # Donation milestones
        if self.total_donations >= 1 and Badge.FIRST_DONATION not in self.badges:
            new_badges.append(Badge.FIRST_DONATION)
        if self.total_donations >= 5 and Badge.FIVE_DONATIONS not in self.badges:
            new_badges.append(Badge.FIVE_DONATIONS)
        if self.total_donations >= 10 and Badge.TEN_DONATIONS not in self.badges:
            new_badges.append(Badge.TEN_DONATIONS)
        if self.total_donations >= 20 and Badge.HERO not in self.badges:
            new_badges.append(Badge.HERO)
        if self.total_donations >= 30 and Badge.LIFESAVER not in self.badges:
            new_badges.append(Badge.LIFESAVER)
        
        # Streak badges
        if self.current_donation_streak >= 6 and Badge.CONSISTENT not in self.badges:
            new_badges.append(Badge.CONSISTENT)
        
        # SOS engagement badges
        if self.sos_responses >= 3 and Badge.EMERGENCY_RESPONDER not in self.badges:
            new_badges.append(Badge.EMERGENCY_RESPONDER)
        if self.successful_sos_responses >= 5 and Badge.TRUSTED_DONOR not in self.badges:
            new_badges.append(Badge.TRUSTED_DONOR)
        
        # Add new badges
        for badge in new_badges:
            if badge not in self.badges:
                self.badges.append(badge)
                self.points += 50  # Award points for each badge
        
        if new_badges:
            self.save()
        
        return new_badges

    def get_badge_display(self):
        """Return badge objects with details"""
        badge_data = []
        for badge_key in self.badges:
            badge_data.append({
                'key': badge_key,
                'label': dict(Badge.choices).get(badge_key, badge_key),
            })
        return badge_data
