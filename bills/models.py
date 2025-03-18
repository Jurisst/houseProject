from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

class MeterReading(models.Model):
    meter = models.ForeignKey(
        'Meter', 
        on_delete=models.CASCADE,
        related_name='readings'
    )
    reading_date = models.DateField(_("Reading Date"))
    reading_value = models.DecimalField(
        _("Reading Value"),
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text=_("Current meter reading value")
    )
    is_verified = models.BooleanField(_("Verified"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reading_date', 'meter']
        unique_together = ['meter', 'reading_date']
        verbose_name = _("Meter Reading")
        verbose_name_plural = _("Meter Readings")
        indexes = [
            models.Index(fields=['reading_date', 'meter']),
        ]

    def __str__(self):
        return f"{self.meter} - {self.reading_date}: {self.reading_value}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Check if reading is greater than previous reading
        previous_reading = MeterReading.objects.filter(
            meter=self.meter,
            reading_date__lt=self.reading_date
        ).order_by('-reading_date').first()

        if previous_reading and self.reading_value < previous_reading.reading_value:
            raise ValidationError({
                'reading_value': _("New reading cannot be less than previous reading")
            }) 